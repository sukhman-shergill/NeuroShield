"""
Central configuration for the Hybrid CNN-LSTM Network Traffic Intelligence Engine.
All paths, hyperparameters, and settings are defined here.

This system is optimized exclusively for the UNSW-NB15 dataset (modern, realistic network traffic).
"""

import os

# IMPORTANT: Set Keras backend to TensorFlow before any TF/Keras imports.
# Keras 3.x defaults to trying PyTorch first, which we don't need.
os.environ["KERAS_BACKEND"] = "tensorflow"

# ---------------------------------------------------------------------------
# Project root directory (auto-detected from this file's location)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Directory paths (auto-created at runtime)
# ---------------------------------------------------------------------------
DATA_DIR          = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR      = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR        = os.path.join(PROJECT_ROOT, "models")
OUTPUTS_DIR       = os.path.join(PROJECT_ROOT, "outputs")
LOGS_DIR          = os.path.join(PROJECT_ROOT, "logs")
NOTEBOOKS_DIR     = os.path.join(PROJECT_ROOT, "notebooks")

for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR,
                 OUTPUTS_DIR, LOGS_DIR, NOTEBOOKS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ---------------------------------------------------------------------------
# Active dataset selection (UNSW-NB15 is the only supported dataset)
# ---------------------------------------------------------------------------
ACTIVE_DATASET = "unsw-nb15"

# ---------------------------------------------------------------------------
# UNSW-NB15 Dataset (modern, realistic network traffic — 2015)
# Place CSV files in data/raw/ before training:
#   UNSW_NB15_training-set.csv
#   UNSW_NB15_testing-set.csv
# Available from: https://research.unsw.edu.au/projects/unsw-nb15-dataset
# Also on Kaggle: https://www.kaggle.com/datasets/mrwellsdavid/unsw-nb15
# ---------------------------------------------------------------------------
TRAIN_FILE = os.path.join(RAW_DATA_DIR, "UNSW_NB15_training-set.csv")
TEST_FILE  = os.path.join(RAW_DATA_DIR, "UNSW_NB15_testing-set.csv")

# UNSW-NB15 feature columns (42 features — excludes id, label, attack_cat)
FEATURE_NAMES = [
    "dur", "proto", "service", "state", "spkts", "dpkts", "sbytes",
    "dbytes", "rate", "sttl", "dttl", "sload", "dload", "sloss", "dloss",
    "sinpkt", "dinpkt", "sjit", "djit", "swin", "stcpb", "dtcpb", "dwin",
    "tcprtt", "synack", "ackdat", "smean", "dmean", "trans_depth",
    "response_body_len", "ct_srv_src", "ct_state_ttl", "ct_dst_ltm",
    "ct_src_dport_ltm", "ct_dst_sport_ltm", "ct_dst_src_ltm",
    "is_ftp_login", "ct_ftp_cmd", "ct_flw_http_mthd", "ct_src_ltm",
    "ct_srv_dst", "is_sm_ips_ports",
]
CATEGORICAL_FEATURES = ["proto", "service", "state"]

# UNSW-NB15 has 9 attack categories. We map them to a clean 5-class schema
# for architecture compatibility and balanced evaluation.
ATTACK_MAPPING = {
    "Normal":        "Normal",
    "DoS":           "DoS",
    "Fuzzers":       "Probe",    # Fuzzing = reconnaissance/scanning behaviour
    "Reconnaissance":"Probe",
    "Analysis":      "Probe",    # Port/content analysis
    "Generic":       "Probe",    # Generic attack attempts
    "Exploits":      "R2L",      # Exploitation of remote vulnerabilities
    "Backdoors":     "R2L",      # Remote access backdoors
    "Shellcode":     "U2R",      # Shellcode = privilege escalation
    "Worms":         "U2R",      # Worm propagation (self-replicating, local)
}

# UNSW-NB15 skewed features to log-transform
SKEWED_COLS = [
    "dur", "sbytes", "dbytes", "rate", "sload", "dload",
    "smean", "dmean", "response_body_len",
]

# ---------------------------------------------------------------------------
# Shared class label configuration (in alphabetical order to match LabelEncoder)
# ---------------------------------------------------------------------------
CLASS_NAMES  = ["DoS", "Normal", "Probe", "R2L", "U2R"]
NUM_CLASSES  = len(CLASS_NAMES)

# ---------------------------------------------------------------------------
# Sequence building parameters
# ---------------------------------------------------------------------------
SEQUENCE_LENGTH = 10  # Number of consecutive records per sequence

# ---------------------------------------------------------------------------
# Model hyperparameters
# ---------------------------------------------------------------------------
# CNN layers
CNN_FILTERS_1    = 64
CNN_KERNEL_SIZE_1 = 3
CNN_FILTERS_2    = 128
CNN_KERNEL_SIZE_2 = 3
POOL_SIZE        = 2

# LSTM layers
LSTM_UNITS_1 = 128   # Bidirectional LSTM
LSTM_UNITS_2 = 64    # Second LSTM (unused in current architecture — reserved)

# Dense layers
DENSE_UNITS      = 128
DROPOUT_RATE     = 0.2
L2_REGULARIZATION = 1e-5

# ---------------------------------------------------------------------------
# Focal Loss hyperparameters
# ---------------------------------------------------------------------------
# gamma=2.0: standard value from Lin et al. RetinaNet paper
# alpha=1.0: placeholder — overridden at runtime by square-root class weights
# label_smoothing=0.05: soft targets, prevents overconfident majority-class predictions
FOCAL_LOSS_GAMMA    = 2.0
FOCAL_LOSS_ALPHA    = 1.0
LABEL_SMOOTHING     = 0.05

# ---------------------------------------------------------------------------
# Training parameters
# ---------------------------------------------------------------------------
BATCH_SIZE              = 256    # ↑ from 128: larger batches → smoother gradients, better minority-class representation per batch
EPOCHS                  = 60
LEARNING_RATE           = 0.001  # ↑ from 0.0005: faster warm-start; ReduceLROnPlateau decays it
EARLY_STOPPING_PATIENCE = 15    # ↑ from 12: more room to recover after LR reductions
REDUCE_LR_PATIENCE      = 6     # ↑ from 5: fewer premature LR drops
REDUCE_LR_FACTOR        = 0.5
VALIDATION_SPLIT        = 0.15

# ---------------------------------------------------------------------------
# Saved model and artifact paths
# ---------------------------------------------------------------------------
MODEL_SAVE_PATH           = os.path.join(MODELS_DIR, "cnn_lstm_model.keras")
SCALER_SAVE_PATH          = os.path.join(MODELS_DIR, "scaler.joblib")
LABEL_ENCODERS_SAVE_PATH  = os.path.join(MODELS_DIR, "label_encoders.joblib")
TRAINING_HISTORY_PATH     = os.path.join(OUTPUTS_DIR, "training_history.json")
CLASSIFICATION_REPORT_PATH = os.path.join(OUTPUTS_DIR, "classification_report.json")
PER_CLASS_METRICS_PATH    = os.path.join(OUTPUTS_DIR, "per_class_metrics.json")
CONFUSION_MATRIX_PATH     = os.path.join(OUTPUTS_DIR, "confusion_matrix.png")
TRAINING_CURVES_PATH      = os.path.join(OUTPUTS_DIR, "training_curves.png")
ROC_CURVES_PATH           = os.path.join(OUTPUTS_DIR, "roc_curves.png")
ATTACK_DISTRIBUTION_PATH  = os.path.join(OUTPUTS_DIR, "attack_distribution.png")
MODEL_METADATA_PATH       = os.path.join(MODELS_DIR, "model_metadata.json")

# ---------------------------------------------------------------------------
# API configuration
# ---------------------------------------------------------------------------
API_HOST = "0.0.0.0"
API_PORT = 5000

# Allowed CORS origins (comma-separated via env var for production security)
# Example: NEUROSHIELD_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ALLOWED_ORIGINS = os.environ.get(
    "NEUROSHIELD_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
