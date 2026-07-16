"""
Source package for the Hybrid CNN-LSTM Network Traffic Intelligence Engine.

Modules:
    data_loader    - UNSW-NB15 dataset loader
    preprocessor   - Feature engineering pipeline (no oversampling)
    sequence_builder - Sliding window sequence construction
    model          - CNN-LSTM-Attention architecture
    losses         - FocalLoss for class-imbalanced training
    metrics        - MacroF1Score custom metric
    predictor      - Inference engine with sliding window buffer
    evaluator      - Evaluation metrics, plots, and JSON outputs
    explainer      - Attention + feature importance explainability
"""
