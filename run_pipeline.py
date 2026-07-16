"""
Main entry point for the Hybrid CNN-LSTM Network Traffic Intelligence Engine.

Usage:
    python run_pipeline.py --mode train               Train the model on UNSW-NB15
    python run_pipeline.py --mode train --dry-run     Validate pipeline without training
    python run_pipeline.py --mode evaluate            Evaluate saved model
    python run_pipeline.py --mode predict             Run inference demo
    python run_pipeline.py --mode api                 Start REST API server
"""

import argparse
import sys
import os
import json

import numpy as np

import config
from utils.logger import get_logger

logger = get_logger(__name__)


def run_training(dry_run: bool = False) -> None:
    """Load data, preprocess, build sequences, compile and train the model."""
    logger.info("=" * 70)
    logger.info(f"  Mode: TRAINING | Dataset: {config.ACTIVE_DATASET.upper()}")
    if dry_run:
        logger.info("  DRY RUN — pipeline validation only, no training will occur")
    logger.info("=" * 70)

    import tensorflow as tf
    from src.data_loader import load_train_test
    from src.preprocessor import DataPreprocessor
    from src.sequence_builder import build_sequences
    from src.model import build_model, AttentionLayer
    from src.losses import FocalLoss
    from src.metrics import MacroF1Score
    from datetime import datetime
    from sklearn.model_selection import train_test_split

    # 1. Load dataset
    logger.info("Loading datasets...")
    train_df, test_df = load_train_test()

    if dry_run:
        logger.info(f"Dry run: train={len(train_df)}, test={len(test_df)} records loaded OK.")
        logger.info("Dry run: preprocessing check...")

    # 2. Preprocess — fit scaler on train set, transform train and test
    logger.info("Preprocessing datasets (flat scaling)...")
    preprocessor = DataPreprocessor()
    X_train_flat, y_train_flat, X_test_flat, y_test_flat = preprocessor.fit_transform(
        train_df, test_df
    )
    preprocessor.save_transformers()

    if dry_run:
        logger.info(
            f"Dry run: preprocessed flat shapes → "
            f"X_train={X_train_flat.shape}, X_test={X_test_flat.shape}"
        )
        logger.info("Dry run complete. Pipeline is valid. Run without --dry-run to train.")
        return

    # 3. Build sequences chronologically (sliding window) to preserve local packet relations
    logger.info("Building sliding-window sequences chronologically...")
    X_train_seq_all, y_train_seq_all = build_sequences(X_train_flat, y_train_flat)
    X_test_seq, y_test_seq           = build_sequences(X_test_flat, y_test_flat)

    # 4. Split sequences randomly (stratified) into train and validation splits
    #    This prevents validation set homogeneity (unbalanced class distributions)
    #    while keeping sequence context inside each window intact.
    logger.info("Splitting sequences into stratified train and validation splits...")
    y_train_idx = np.argmax(y_train_seq_all, axis=1)
    X_train_seq, X_val_seq, y_train_seq, y_val_seq = train_test_split(
        X_train_seq_all,
        y_train_seq_all,
        test_size=config.VALIDATION_SPLIT,
        random_state=42,
        stratify=y_train_idx,
    )

    logger.info(
        f"Sequence splits ready → "
        f"Train: {X_train_seq.shape}, Val: {X_val_seq.shape}, Test: {X_test_seq.shape}"
    )

    # 5. Compute square-root frequency class weights to balance Focal Loss alpha
    unique_classes, counts = np.unique(y_train_flat, return_counts=True)
    sqr_counts = np.sqrt(counts)
    sum_sqr = np.sum(sqr_counts)
    sqr_weights = (sum_sqr / (config.NUM_CLASSES * sqr_counts)).tolist()
    logger.info(f"Computed square-root class weights: {dict(zip(config.CLASS_NAMES, sqr_weights))}")

    # 6. Build and compile model
    input_shape = (X_train_seq.shape[1], X_train_seq.shape[2])
    model = build_model(input_shape, class_weights=sqr_weights)

    # 7. Callbacks
    #    EarlyStopping monitors val_macro_f1 (mode='max') instead of val_loss.
    #    This ensures the best saved checkpoint maximises class-balanced detection.
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_macro_f1",
            mode="max",
            patience=config.EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=config.MODEL_SAVE_PATH,
            monitor="val_macro_f1",
            mode="max",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_macro_f1",
            mode="max",
            factor=config.REDUCE_LR_FACTOR,
            patience=config.REDUCE_LR_PATIENCE,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    # 8. Train
    logger.info("Training model...")
    start_time = datetime.now()
    history = model.fit(
        X_train_seq,
        y_train_seq,
        epochs=config.EPOCHS,
        batch_size=config.BATCH_SIZE,
        validation_data=(X_val_seq, y_val_seq),
        callbacks=callbacks,
        verbose=1,
    )
    training_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Training completed in {training_time:.1f}s")

    # 9. Save metadata
    with open(config.MODEL_METADATA_PATH, "w") as f:
        json.dump({
            "model_name":            "CNN_LSTM_Attention_IDS",
            "trained_at":            datetime.now().isoformat(),
            "training_time_seconds": training_time,
            "total_epochs_trained":  len(history.history["loss"]),
            "input_shape":           list(input_shape),
            "num_classes":           config.NUM_CLASSES,
            "class_names":           config.CLASS_NAMES,
            "sequence_length":       config.SEQUENCE_LENGTH,
            "dataset_used":          config.ACTIVE_DATASET,
            "loss_function":         "FocalLoss",
            "focal_gamma":           config.FOCAL_LOSS_GAMMA,
            "focal_alpha":           sqr_weights,
            "early_stopping_monitor":"val_macro_f1",
        }, f, indent=2)

    history_data = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    with open(config.TRAINING_HISTORY_PATH, "w") as f:
        json.dump(history_data, f)

    # 10. Evaluate
    logger.info("Evaluating on test set...")
    from src.evaluator import evaluate_model
    from utils.visualization import generate_all_visualizations

    report = evaluate_model(model, X_test_seq, y_test_seq)
    generate_all_visualizations()

    logger.info("\nTraining and Evaluation Complete.")
    logger.info(f"Overall Accuracy:  {report.get('overall_accuracy', 0.0):.4f}")
    logger.info(f"Weighted F1:       {report.get('weighted_f1', 0.0):.4f}")
    logger.info(f"Macro F1:          {report.get('macro_f1', 0.0):.4f}")


def run_evaluation() -> None:
    """Evaluate a saved model on the test dataset."""
    logger.info("=" * 70)
    logger.info(f"  Mode: EVALUATION | Dataset: {config.ACTIVE_DATASET.upper()}")
    logger.info("=" * 70)

    import tensorflow as tf
    from src.data_loader import load_train_test
    from src.preprocessor import DataPreprocessor
    from src.sequence_builder import build_sequences
    from src.evaluator import evaluate_model
    from src.model import AttentionLayer
    from src.losses import FocalLoss
    from src.metrics import MacroF1Score
    from utils.visualization import generate_all_visualizations

    _, test_df = load_train_test()

    preprocessor = DataPreprocessor()
    preprocessor.load_transformers()
    X_test, y_test = preprocessor.transform_df(test_df)

    # Build test sequences chronologically (no flat shuffling)
    X_test_seq, y_test_seq = build_sequences(X_test, y_test)

    from src.model import build_model
    with open(config.MODEL_METADATA_PATH, "r") as f:
        metadata = json.load(f)
    input_shape = tuple(metadata["input_shape"])
    model = build_model(input_shape=input_shape)
    model.load_weights(config.MODEL_SAVE_PATH)

    report = evaluate_model(model, X_test_seq, y_test_seq)
    generate_all_visualizations()

    logger.info(f"\nOverall Accuracy:  {report.get('overall_accuracy', 'N/A'):.4f}")
    logger.info(f"Weighted F1:       {report.get('weighted_f1', 'N/A'):.4f}")
    logger.info(f"Macro F1:          {report.get('macro_f1', 'N/A'):.4f}")


def run_prediction() -> None:
    """Run inference on sample test records to demonstrate the predictor."""
    logger.info("=" * 70)
    logger.info("  Mode: PREDICTION")
    logger.info("=" * 70)

    from src.data_loader import load_train_test
    from src.predictor import AttackPredictor

    predictor = AttackPredictor()
    _, test_df = load_train_test()

    logger.info("\nRunning predictions on sample records...\n")

    sample_records = []
    for category in config.CLASS_NAMES:
        subset = test_df[test_df["attack_category"] == category]
        if len(subset) > 0:
            sample_records.append(subset.iloc[0])

    # Warm up the sliding window buffer with real context
    predictor.reset_buffer()
    for _, row in test_df.iloc[: config.SEQUENCE_LENGTH].iterrows():
        rec = {k: v for k, v in row.to_dict().items()
               if k not in ["label", "attack_category", "difficulty_level"]}
        predictor.predict_record(rec)

    logger.info("Buffer warmed up. Running predictions on sample records...\n")
    for record_series in sample_records:
        record = record_series.to_dict()
        actual = record.get("attack_category", "Unknown")
        pred_record = {
            k: v for k, v in record.items()
            if k not in ["label", "attack_category", "difficulty_level"]
        }
        result = predictor.predict_record(pred_record)
        logger.info(
            f"Actual: {actual:8s} | "
            f"Predicted: {result['predicted_class']:8s} | "
            f"Confidence: {result['confidence']:.4f}"
        )

    logger.info("\nPrediction complete.")


def run_api() -> None:
    """Start the Flask REST API server."""
    from api.engine import start_api
    start_api()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hybrid CNN-LSTM Network Traffic Intelligence Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["train", "evaluate", "predict", "api"],
        help="Operation mode",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the pipeline (data loading, preprocessing) without training",
    )

    args = parser.parse_args()

    if args.mode == "train":
        run_training(dry_run=args.dry_run)
    elif args.mode == "evaluate":
        run_evaluation()
    elif args.mode == "predict":
        run_prediction()
    elif args.mode == "api":
        run_api()


if __name__ == "__main__":
    main()
