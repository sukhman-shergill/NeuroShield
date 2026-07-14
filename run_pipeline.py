"""
Main entry point for the Hybrid CNN-LSTM Network Traffic Intelligence Engine.

Usage:
    python run_pipeline.py --mode train      Train the model on the NSL-KDD dataset
    python run_pipeline.py --mode evaluate   Evaluate saved model on test data
    python run_pipeline.py --mode predict    Run inference using the trained model
    python run_pipeline.py --mode api        Start the REST API server
"""

import argparse
import sys
import os
import json

import numpy as np

import config
from utils.logger import get_logger

logger = get_logger(__name__)


def run_training():
    """Download data, preprocess, build sequences, compile and train the model."""
    logger.info("=" * 70)
    logger.info("  Mode: TRAINING (With Balanced Oversampling)")
    logger.info("=" * 70)

    import tensorflow as tf
    from src.data_loader import load_train_test
    from src.preprocessor import DataPreprocessor
    from src.sequence_builder import build_sequences
    from src.model import build_model, AttentionLayer
    from datetime import datetime
    from sklearn.utils.class_weight import compute_class_weight

    # 1. Download and load train and test datasets
    logger.info("Loading training and testing data...")
    train_df, test_df = load_train_test()

    # 2. Preprocess data (Split train & val BEFORE oversampling to prevent leakage)
    logger.info("Preprocessing datasets and applying oversampling...")
    preprocessor = DataPreprocessor()
    X_train, y_train, X_val, y_val, X_test, y_test = preprocessor.fit_transform(
        train_df, test_df, val_size=config.VALIDATION_SPLIT
    )
    preprocessor.save_transformers()

    # 3. Build sequences for train, validation, and test splits
    logger.info("Building sequences (sliding window)...")
    X_train_seq, y_train_seq = build_sequences(X_train, y_train)
    X_val_seq, y_val_seq = build_sequences(X_val, y_val)

    shuffle_idx = np.random.RandomState(99).permutation(len(X_test))
    X_test_shuffled = X_test[shuffle_idx]
    y_test_shuffled = y_test[shuffle_idx]
    X_test_seq, y_test_seq = build_sequences(X_test_shuffled, y_test_shuffled)

    # 4. Build and compile model
    input_shape = (X_train_seq.shape[1], X_train_seq.shape[2])
    model = build_model(input_shape)

    # Define callbacks (EarlyStopping, ReduceLROnPlateau, ModelCheckpoint)
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=config.EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=config.MODEL_SAVE_PATH,
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=config.REDUCE_LR_FACTOR,
            patience=config.REDUCE_LR_PATIENCE,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    # Compute class weights on resampled data (just in case there's still slight imbalance)
    y_train_int = np.argmax(y_train_seq, axis=1)
    unique_classes = np.unique(y_train_int)
    weights = compute_class_weight(
        class_weight="balanced",
        classes=unique_classes,
        y=y_train_int,
    )
    class_weights = {int(cls): float(w) for cls, w in zip(unique_classes, weights)}
    logger.info(f"Class weights on resampled data: {class_weights}")

    # 5. Train the model
    logger.info("Training the model...")
    start_time = datetime.now()
    history = model.fit(
        X_train_seq,
        y_train_seq,
        epochs=config.EPOCHS,
        batch_size=config.BATCH_SIZE,
        validation_data=(X_val_seq, y_val_seq),
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1,
    )
    training_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Training completed in {training_time:.1f} seconds")

    # Save training history and model metadata
    with open(config.MODEL_METADATA_PATH, "w") as f:
        json.dump({
            "model_name": "CNN_LSTM_Attention_IDS",
            "trained_at": datetime.now().isoformat(),
            "training_time_seconds": training_time,
            "total_epochs_trained": len(history.history["loss"]),
            "input_shape": list(input_shape),
            "num_classes": config.NUM_CLASSES,
            "class_names": config.CLASS_NAMES,
            "sequence_length": config.SEQUENCE_LENGTH,
            "dataset_used": "nsl-kdd"
        }, f, indent=2)

    # Save history data
    history_data = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    with open(config.TRAINING_HISTORY_PATH, "w") as f:
        json.dump(history_data, f)

    # 6. Evaluate on independent test set
    logger.info("Evaluating on test set...")
    from src.evaluator import evaluate_model
    from utils.visualization import generate_all_visualizations

    report = evaluate_model(model, X_test_seq, y_test_seq)
    generate_all_visualizations()

    logger.info("\nTraining and Evaluation Complete.")
    logger.info(f"Overall Accuracy: {report.get('overall_accuracy', 0.0):.4f}")
    logger.info(f"Weighted F1: {report.get('weighted_f1', 0.0):.4f}")


def run_evaluation():
    """Evaluate a saved model on the test dataset."""
    logger.info("=" * 70)
    logger.info("  Mode: EVALUATION")
    logger.info("=" * 70)

    import tensorflow as tf
    from src.data_loader import load_train_test
    from src.preprocessor import DataPreprocessor
    from src.sequence_builder import build_sequences
    from src.evaluator import evaluate_model
    from src.model import AttentionLayer
    from utils.visualization import generate_all_visualizations

    # Load test data (only need test dataset for evaluation)
    _, test_df = load_train_test()

    # Load saved preprocessing transformers (scaler, label encoders)
    preprocessor = DataPreprocessor()
    preprocessor.load_transformers()

    # Preprocess test data using the loaded transformers
    X_test, y_test = preprocessor.transform_df(test_df)

    # Shuffle test data before building sequences
    shuffle_idx = np.random.RandomState(99).permutation(len(X_test))
    X_test_seq, y_test_seq = build_sequences(X_test[shuffle_idx], y_test[shuffle_idx])

    # Build the model architecture natively to avoid cross-version Keras serialization errors
    from src.model import build_model
    with open(config.MODEL_METADATA_PATH, "r") as f:
        metadata = json.load(f)
    input_shape = tuple(metadata["input_shape"])
    model = build_model(input_shape=input_shape)
    model.load_weights(config.MODEL_SAVE_PATH)

    report = evaluate_model(model, X_test_seq, y_test_seq)
    generate_all_visualizations()

    logger.info(f"\nOverall Accuracy: {report.get('overall_accuracy', 'N/A'):.4f}")
    logger.info(f"Weighted F1: {report.get('weighted_f1', 'N/A'):.4f}")


def run_prediction():
    """Run inference on sample test records to demonstrate the predictor."""
    logger.info("=" * 70)
    logger.info("  Mode: PREDICTION")
    logger.info("=" * 70)

    from src.data_loader import load_train_test
    from src.predictor import AttackPredictor

    # Load the predictor
    predictor = AttackPredictor()

    # Load test data for demonstration
    _, test_df = load_train_test()

    # Pick a few sample records from each class
    logger.info("\nRunning predictions on sample records...\n")

    sample_records = []
    for category in config.CLASS_NAMES:
        subset = test_df[test_df["attack_category"] == category]
        if len(subset) > 0:
            sample = subset.iloc[0]
            sample_records.append(sample)

    # Warm up the predictor buffer with some initial records so the
    # sliding window has real context instead of zero-padding
    predictor.reset_buffer()
    warmup_records = test_df.iloc[:config.SEQUENCE_LENGTH]
    for _, row in warmup_records.iterrows():
        record = row.to_dict()
        pred_record = {
            k: v for k, v in record.items()
            if k not in ["label", "attack_category", "difficulty_level"]
        }
        predictor.predict_record(pred_record)

    # Make predictions on samples from each class
    logger.info("Buffer warmed up. Running predictions on sample records...\n")
    for record_series in sample_records:
        record = record_series.to_dict()
        actual = record.get("attack_category", "Unknown")

        # Remove non-feature fields before prediction
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


def run_api():
    """Start the Flask REST API server."""
    from api.engine import start_api
    start_api()


def main():
    parser = argparse.ArgumentParser(
        description="Hybrid CNN-LSTM Network Traffic Intelligence Engine"
    )
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["train", "evaluate", "predict", "api"],
        help="Operation mode: train, evaluate, predict, or api",
    )

    args = parser.parse_args()

    if args.mode == "train":
        run_training()
    elif args.mode == "evaluate":
        run_evaluation()
    elif args.mode == "predict":
        run_prediction()
    elif args.mode == "api":
        run_api()


if __name__ == "__main__":
    main()
