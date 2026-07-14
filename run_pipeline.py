"""
Main entry point for the Hybrid CNN-LSTM Network Traffic Intelligence Engine.

Usage:
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
        choices=["evaluate", "predict", "api"],
        help="Operation mode: evaluate, predict, or api",
    )

    args = parser.parse_args()

    if args.mode == "evaluate":
        run_evaluation()
    elif args.mode == "predict":
        run_prediction()
    elif args.mode == "api":
        run_api()


if __name__ == "__main__":
    main()
