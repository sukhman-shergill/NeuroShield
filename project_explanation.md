# NeuroShield NIDS — Project Architecture & Explanation Guide

This guide provides a comprehensive explanation of **NeuroShield**, a real-time Network Intrusion Detection System (NIDS) powered by a hybrid **CNN-BiLSTM-Attention** deep learning engine.

---

## 1. Project Overview & Goal

The core goal of **NeuroShield** is to inspect inbound network connection records, classify traffic categories in real-time, detect potential security breaches, and enable rapid mitigation (like host isolation) via a Security Operations Center (SOC) dashboard.

### Dataset Support: UNSW-NB15
NeuroShield is optimized for the **UNSW-NB15** dataset, a modern, realistic network traffic dataset captured from actual network traffic at UNSW Canberra, replacing legacy, simulated datasets.

### Traffic Classification Categories
NeuroShield maps the 9 attack types of UNSW-NB15 into a consolidated **5-class schema** to ensure class-balanced training and sequence-model compatibility:

| Category | Description | UNSW-NB15 Attack Types Mapped | Severity |
|----------|-------------|-------------------------------|----------|
| **Normal** | Safe, standard connection profiles | Normal | Benign |
| **DoS** | Denial of Service vectors aiming at resource exhaustion | DoS | Critical |
| **Probe** | Scanner attempts to discover network structure | Fuzzers, Reconnaissance, Analysis, Generic | High |
| **R2L** | Remote-to-Local unauthorized system access attempts | Exploits, Backdoors | High |
| **U2R** | User-to-Root local privilege escalation attempts | Shellcode, Worms | Critical |

---

## 2. Machine Learning Architecture

The brain of the NIDS is a hybrid model designed in [src/model.py](src/model.py). It merges spatial feature extraction with temporal sequence processing and an attention mechanism focusing.

```
                  ┌──────────────────────────────┐
                  │ Input Sequence (10 × 42)     │
                  └──────────────┬───────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │  CNN spatial patterns        │
                  │  (Conv1D & Max Pool)         │
                  └──────────────┬───────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │  LSTM temporal patterns      │
                  │  (Bidirectional LSTM)        │
                  └──────────────┬───────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │  Attention weighting         │
                  │  (Bahdanau-style weights)    │
                  └──────────────┬───────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │  Dense Classifier            │
                  │  (Softmax dense head)        │
                  └──────────────────────────────┘
```

### Layer-by-Layer Walkthrough
1. **CNN Block (Spatial Feature Extraction)**:
   - Network connection records contain multi-dimensional metrics (e.g., source/destination bytes, packet counts, protocols).
   - A sequence of **Conv1D** layers with Batch Normalization and Spatial Dropout extracts localized feature patterns and correlation coefficients between individual statistics.
2. **LSTM Block (Temporal Sequence Learning)**:
   - Many sophisticated attacks (like slow port scans or brute-force logins) occur over time rather than in a single connection.
   - A **Bidirectional LSTM** captures sequences of consecutive traffic flows, learning temporal correlations in both forward and backward time directions.
3. **Bahdanau-style Attention Mechanism**:
   - The custom **AttentionLayer** learns weights for each sequence step. It computes a tanh-activated score matrix to determine which time steps (connections) are most critical, condensing the sequence into a unified context vector.
4. **Classification Head**:
   - A dense projection layer maps the context vector to a softmax output layer returning probabilities for the 5 target classes.

---

## 3. Data Processing & Sequence Building

Raw data files in [data/raw/](data/raw/) must be converted into standardized floating-point tensors before passing to the model.

### Preprocessing Steps ([src/preprocessor.py](src/preprocessor.py))
- **Log Transform**: Highly skewed quantitative columns (`dur`, `sbytes`, `dbytes`, `rate`, `sload`, `dload`, `smean`, `dmean`, `response_body_len`) undergo an `np.log1p` transformation to reduce outlier variance and prevent gradient saturation.
- **Categorical Encoding**: `proto`, `service`, and `state` are mapped to numbers using `LabelEncoder`.
- **Scaling**: A fitted `StandardScaler` standardizes numeric columns to zero mean and unit variance, fitted **only** on the training split to prevent data leakage.

### Sequence Builder ([src/sequence_builder.py](src/sequence_builder.py))
- The model expects inputs of shape `(batch_size, sequence_length, features)` where `sequence_length = 10`.
- In training, a sliding window processes records into sequences, assigning the label of the **last record** in the window as the target output.
- During inference, if the record buffer contains fewer than 10 entries, **zero-padding** is prepended to ensure structural compatibility.

---

## 4. Backend Architecture ([api/engine.py](api/engine.py))

The backend is built with **Flask** to handle real-time prediction streams, alert routing, server statistics, and process management.

### Thread-Safe Design
Because Flask handles requests concurrently across threads, a thread lock (`_state_lock`) ensures updates to live telemetry queues (e.g. connections, alert dequeues, packets timestamps) are thread-safe and free from race conditions.

### Main API Endpoint Catalogue
- `/predict` & `/predict/batch`: Ingests connection metrics, processes them, runs inference via Keras, updates the SOC telemetry, and logs warning alerts if attacks are detected.
- `/predict/file`: Accepts CSV uploads for bulk log analysis.
- `/stats`: Computes packet rates over the last 10 seconds and virtual memory/CPU load. It utilizes a **5-second caching TTL** for GPU stats (`nvidia-smi`) to avoid system poll overhead.
- `/alerts` & `/alerts/action`: Feeds live security alerts to the frontend and processes isolation/mitigation commands.
- `/simulation/start` & `/simulation/stop`: Spawns and terminates the background simulator script as a subprocess wrapper.

---

## 5. Frontend SOC Dashboard ([frontend/src/](frontend/src/))

The frontend is a React + TypeScript single-page application built on top of Vite and styled with Tailwind CSS and CSS Glassmorphism.

### Key Visual Components
- **Sidebar ([Sidebar.tsx](frontend/src/components/Sidebar.tsx))**: Handles navigation tabs and displays a live dynamic threat count badge.
- **SOC Dashboard View ([DashboardView.tsx](frontend/src/components/DashboardView.tsx))**:
  - **Metrics Cards**: Displays live throughput rate, threat counters, prediction speed, and F1 accuracy curves.
  - **SVG Traffic Chart**: Renders organic bezier-curved path layers showing real-time network load vs blocked alerts.
  - **Donut Chart Breakdown**: Renders SVG circular segments mapping attack distribution using memoized offsets to prevent StrictMode rendering overlaps.
  - **Mitigation Table**: Lists detected threats with action controllers (`ISOLATE` or `REVIEW`) and an interactive Hex Packet inspector modal.

---

## 6. End-to-End Testing Loop ([simulate_attacks.py](simulate_attacks.py))

To inspect the system in action, `simulate_attacks.py` loads the UNSW-NB15 test partition, serializes numeric/numpy features correctly, assigns source/destination IPs (anomalous external IPs for attack classes, internal range IPs for normal traffic), and posts requests to the API.

This triggers the following pipeline:
```
[Simulator] ──(JSON payload)──► [Flask Engine] ──► [Preprocessor]
                                     │                  │
                                     ▼                  ▼
[Dashboard] ◄──(GET /api/stats)── [SOC Queue] ◄── [CNN-BiLSTM Engine]
```
