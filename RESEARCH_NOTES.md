# NeuroShield — Architecture Decision Record

> This document explains every significant technical decision made in the NeuroShield NIDS project.
> Understanding *why* these choices were made is as important as understanding *what* was built.

---

## 1. Why CNN-LSTM-Attention Over a Pure LSTM or Transformer?

**Decision**: Use a hybrid CNN → BiLSTM → Attention architecture.

**Reasoning**:

- **Pure LSTM** processes each feature sequentially, treating the 42 UNSW-NB15 features as a 1D time series. But the features have *spatial correlations* — packet sizes (`sbytes`, `dbytes`) and transmission rates (`sload`, `dload`) are closely related. An LSTM processes these sequentially, never explicitly modeling their inter-feature relationships.

- **Conv1D layers** act as a feature correlation extractor — they compute local weighted sums across groups of features using learned kernels, similar to how CNNs detect edges in images. This gives the LSTM a richer input representation than raw features.

- **Pure Transformer (self-attention)**: Would work well on longer sequences, but our sequence length is 10 records — short enough that the BiLSTM captures temporal dependencies efficiently. Transformers also require much more data to train stably and don't generalize well on our ~175K samples.

- **Our hybrid** gets the best of both: CNN extracts spatial feature correlations, LSTM captures temporal attack progression patterns, Attention identifies which specific time steps in the sequence were most attack-indicative.

**Alternatives rejected**: Transformer (data-hungry), GRU (simpler but weaker expressiveness), pure Dense (no temporal modelling).

---

## 2. Why Sequence Length = 10?

**Decision**: Each input to the model is a sliding window of 10 consecutive connection records.

**Reasoning**:

- **Slow-burn attacks**: Probe attacks (reconnaissance scans like fuzzers, scanning, analysis) typically manifest across multiple connection events — you can't classify a single packet as a port scan, you need to see the pattern of many connections to the same host from the same source. A window of 10 captures this without being too long.

- **Memory efficiency**: Sequence length × feature count × batch size determines the memory footprint during training. Length 10 × 42 features × 256 batch = 107,520 float32 values per batch, which fits comfortably in GPU VRAM.

- **Empirical validation**: Values of 5, 10, and 20 were tested. Length 10 produced the best validation macro F1. Longer windows (20+) created much more training data but didn't improve performance due to label noise in longer windows (the label of a window is the label of the last record; earlier records in a DoS window may be legitimate connection records before the attack started).

---

## 3. Why Bidirectional LSTM Before the Attention Layer?

**Decision**: Use a `Bidirectional(LSTM(128, return_sequences=True))` rather than a unidirectional LSTM.

**Reasoning**:

In real-time intrusion detection, we process a *buffered window* of 10 records at once, not a true real-time stream. Within this window, we have access to both past and future context relative to any given record. A BiLSTM processes the sequence in both directions and concatenates the hidden states, giving the attention layer a 256-dimensional representation (128 forward + 128 backward) per time step.

This is especially valuable for attack patterns that have a distinct setup and teardown phase.

**Why not before the CNN?**: The CNN needs to see raw features to extract spatial correlations. Feeding LSTM output into CNN would lose interpretability and the local feature structure.

---

## 4. Why SpatialDropout1D in CNN Blocks (Not Regular Dropout)?

**Decision**: Use `SpatialDropout1D(0.2)` after each Conv1D block.

**Reasoning**:

Regular `Dropout` drops individual values randomly, which can destroy a feature map while keeping its neighbours. For 1D convolutional feature maps, adjacent time steps are highly correlated — if one feature map value is dropped, its neighbours provide redundant information, so the regularization effect is weak.

`SpatialDropout1D` drops entire *feature map channels* at once. If a CNN filter's entire output channel is dropped, the network must learn to be robust to losing any single feature extraction pattern. This produces significantly better regularization for sequence data.

Reference: Tompson et al., "Efficient Object Localization Using CNNs" (2015).

---

## 5. Why StandardScaler Over MinMaxScaler?

**Decision**: Use `StandardScaler` (zero mean, unit variance) for feature normalization.

**Reasoning**:

- UNSW-NB15 network features like `sbytes` and `dbytes` are extremely right-skewed and contain outliers. MinMaxScaler would compress all normal traffic into a tiny range near zero, making the normal class hard to learn.

- StandardScaler is robust to extreme outliers in the sense that a single large value doesn't compress the entire feature range — it only shifts the mean and standard deviation slightly.

- The LSTM and Dense layers benefit from approximately zero-mean inputs for stable gradient flow.

**Note**: We apply StandardScaler *after* the train/val split to prevent data leakage — see decision #7.

---

## 6. Why log1p Transform for dur, sbytes, dbytes, rate?

**Decision**: Apply `np.log1p(x)` to highly skewed numeric features before scaling.

**Reasoning**:

The distributions of `sbytes`, `dbytes`, `dur`, and `rate` are heavily right-skewed. DoS attacks have `sbytes` near zero (SYN flood with no payload) while normal file transfers have millions of bytes. Without transformation:

- StandardScaler produces a range where 99.9% of samples cluster near zero and a few extreme values dominate.
- The model's gradients are dominated by outliers, leading to poor generalization.

`log1p(x) = log(x + 1)` compresses the scale while handling zeros gracefully (`log1p(0) = 0`). After transformation, the distribution is approximately Gaussian, which is optimal for StandardScaler.

---

## 7. Why Train/Validation Split BEFORE Scaler Fitting?

**Decision**: Split training data into train and validation sets, then fit the scaler **only** on the training split.

**Reasoning**:

This is a fundamental data leakage prevention requirement. If you fit the scaler on the entire training set (including validation), the validation mean and standard deviation "leaks" into the scaler. When you then use validation loss to evaluate the model, you're evaluating on data the preprocessing pipeline has already seen — leading to optimistic validation metrics that don't generalize.

The correct order:
```
raw_train → train_test_split → (train_split, val_split)
                                     ↓
                              scaler.fit(train_split)
                                     ↓
                              scaler.transform(train_split)
                              scaler.transform(val_split)   ← no leakage
                              scaler.transform(test_split)  ← no leakage
```

Many public ML notebooks get this wrong by calling `scaler.fit_transform(X)` on all data before the split.

---

## 8. Why Focal Loss Instead of RandomOverSampler?

**Decision**: Use `FocalLoss(gamma=2.0, alpha=0.25)` + `compute_class_weight` instead of RandomOverSampling for class imbalance.

**Reasoning**:

Oversampling duplicates flat records. In sequence models, this creates overlapping windows where the same record appears multiple times sequentially, producing artificial temporal patterns that don't exist in real network traffic.

**Focal Loss** (Lin et al., RetinaNet 2017) solves imbalance at the loss level:
- `FL(p_t) = -alpha * (1 - p_t)^gamma * log(p_t)`
- When `p_t` is high (easy, majority-class sample): `(1-p_t)^gamma → 0`, loss is suppressed
- When `p_t` is low (hard, minority-class sample): `(1-p_t)^gamma → 1`, full loss applied
- The model is forced to focus on rare samples without any synthetic data

Combined with `sklearn.compute_class_weight("balanced")` and, more recently, **square-root frequency class weights** (Cui et al. 2019) passed as the per-class `alpha` vector, this gives a strong signal for minority classes without distorting the data distribution.

---

## 9. Why Monitor val_macro_f1 for EarlyStopping?

**Decision**: `EarlyStopping(monitor="val_macro_f1", mode="max")` instead of `monitor="val_loss"`.

**Reasoning**:

Monitoring `val_loss` (Focal Loss value) can be misleading. As the model improves on normal traffic, the loss decreases — but rare classes may still be undetected.

Macro F1 treats all 5 classes equally. A macro F1 of 0.70 means the model has reasonable performance on *all* classes, not just the dominant ones. When macro F1 is the EarlyStopping criterion, the best saved checkpoint is guaranteed to be the one with the best *class-balanced* detection capability.

---

## 10. Why UNSW-NB15?

**Decision**: UNSW-NB15 is a modern, realistic network dataset captured from actual network traffic at UNSW Canberra, replacing legacy, simulated datasets.

- The 5-class schema (Normal, DoS, Probe, R2L, U2R) is maintained via the attack category mapping in `config.py`.

---

## 11. Why Cube-Root Class Weights Instead of Pure Focal Loss?

**Decision**: Pass per-class cube-root frequency weights as the `alpha` vector in `FocalLoss`.

**Reasoning**:

Pure Focal Loss (scalar `alpha`) suppresses easy samples via the `(1-p_t)^gamma` term but treats all classes equally in gradient magnitude. With UNSW-NB15, `Normal` accounts for ~40% of samples and `U2R` for ~0.3%. 

**Inverse-frequency weighting** (`w_c ∝ 1/N_c`) fixes this but produces extreme ratios (U2R/Normal ≈ 87×), causing gradient explosion and high false positive rates for rare classes.

**Square-root frequency scaling** (Cui et al., CVPR 2019) provides a robust minority-class signal but was found to overly penalize the dominant `Normal` class, pulling overall accuracy below 80%.

**Cube-root frequency scaling** (`∛N_c`) flattens the weights further towards uniform. This balances the Focal Loss penalty by boosting the accuracy on the majority classes (`Normal` and `Probe`) without losing the ability to detect `DoS` and `U2R`. This modification was essential to break the 80% overall accuracy threshold.

---

## 12. Why Label Smoothing (ε=0.05)?

**Decision**: Apply label smoothing with ε=0.05 inside `FocalLoss.call()`.

**Reasoning**:

Without label smoothing, the model's softmax becomes extremely overconfident on the dominant classes (Normal/Probe precision → 0.90+). This manifests as very high precision but low recall on minority classes: the model is reluctant to predict `DoS` or `U2R` unless it is extremely certain, which rarely happens due to the imbalanced training signal.

Label smoothing replaces hard one-hot targets `y_true` with:
```
y_smooth = y_true * (1 - ε) + ε / K
```
where `K` is the number of classes. With ε=0.05 and K=5, the true class has target 0.96 and each other class has target 0.01. This:
1. Prevents the loss from being driven entirely to zero for correctly classified easy samples
2. Forces the model to maintain a small residual probability mass across all classes
3. Improves calibration — the output probabilities better reflect actual uncertainty

ε=0.05 is the standard value from Szegedy et al. ("Rethinking the Inception Architecture", 2016). Values above 0.1 start to harm overall accuracy.

---

## References

1. Lin, T.-Y., et al. "Focal Loss for Dense Object Detection." ICCV 2017. (RetinaNet)
2. Moustafa, N., & Slay, J. "UNSW-NB15: a comprehensive data set for network intrusion detection systems." MilCIS 2015.
3. Tompson, J., et al. "Efficient Object Localization Using CNNs." CVPR 2015. (SpatialDropout)
4. Bahdanau, D., et al. "Neural Machine Translation by Jointly Learning to Align and Translate." ICLR 2015. (Attention)
5. Cui, Y., et al. "Class-Balanced Loss Based on Effective Number of Samples." CVPR 2019. (Square-Root Weighting)
6. Szegedy, C., et al. "Rethinking the Inception Architecture for Computer Vision." CVPR 2016. (Label Smoothing)
