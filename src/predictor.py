"""
Inference predictor for the CNN-LSTM intrusion detection model.

Loads a trained model and preprocessor transformers, then classifies
new network connection records.
"""

import os

import numpy as np
import pandas as pd
import tensorflow as tf

import config
from src.preprocessor import DataPreprocessor
from src.sequence_builder import build_single_sequence
from src.model import AttentionLayer
from utils.logger import get_logger

logger = get_logger(__name__)


class AttackPredictor:
    """
    Inference engine for classifying network traffic.

    Loads the trained model and preprocessor, then provides methods
    to classify individual records or batches of records.
    """

    def __init__(self, model_path: str = None):
        """
        Initialize the predictor by loading model and transformers.

        Args:
            model_path: Path to saved model. Defaults to config.MODEL_SAVE_PATH.
        """
        if model_path is None:
            model_path = config.MODEL_SAVE_PATH

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Trained model not found at {model_path}. "
                "Run training first: python run_pipeline.py --mode train"
            )

        logger.info(f"Loading model weights from {model_path}")
        
        # Build the model architecture natively to avoid cross-version Keras serialization errors
        from src.model import build_model
        
        # We need the input shape. Since SEQUENCE_LENGTH is 10 and features are 41 (mapped down)
        # We can dynamically determine features or just use a dummy build shape.
        # But wait, config.SEQUENCE_LENGTH and features are known.
        
        # Get metadata to know exact input shape
        import json
        with open(config.MODEL_METADATA_PATH, "r") as f:
            metadata = json.load(f)
            
        input_shape = tuple(metadata["input_shape"])
        self.model = build_model(input_shape=input_shape)
        
        # Load weights into the architecture
        self.model.load_weights(model_path)

        self.preprocessor = DataPreprocessor()
        self.preprocessor.load_transformers()

        # Buffer for building sequences (accumulates recent records)
        self._record_buffer = []

        logger.info("Predictor initialized successfully.")

    def predict_record(self, record: dict) -> dict:
        """
        Classify a single network connection record.

        The record is added to an internal buffer. If enough records
        are accumulated, a sequence is built and classified. Otherwise,
        zero-padding is used to complete the sequence.

        Args:
            record: Dictionary with UNSW-NB15 feature names as keys.

        Returns:
            Dictionary with:
            - predicted_class: The predicted attack category name
            - confidence: Confidence score for the predicted class
            - all_probabilities: Dict of class name -> probability for all classes
        """
        # Transform the record
        features = self.preprocessor.transform_single(record)

        # Add to buffer
        self._record_buffer.append(features)

        # Keep only the last SEQUENCE_LENGTH records
        if len(self._record_buffer) > config.SEQUENCE_LENGTH:
            self._record_buffer = self._record_buffer[-config.SEQUENCE_LENGTH:]

        # Build sequence (will pad if buffer is smaller than sequence_length)
        buffer_array = np.array(self._record_buffer, dtype=np.float32)
        sequence = build_single_sequence(buffer_array, config.SEQUENCE_LENGTH)

        # Predict
        probabilities = self.model.predict(sequence, verbose=0)[0]
        predicted_class_idx = int(np.argmax(probabilities))
        
        # Dynamically map indices using the loaded target encoder classes to prevent label swapping
        class_labels = self.preprocessor.target_encoder.classes_
        predicted_class = class_labels[predicted_class_idx]
        confidence = float(probabilities[predicted_class_idx])

        result = {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "all_probabilities": {
                name: float(prob)
                for name, prob in zip(class_labels, probabilities)
            },
        }

        logger.debug(f"Prediction: {predicted_class} ({confidence:.4f})")
        return result

    def predict_batch(self, records: list[dict]) -> list[dict]:
        """
        Classify a batch of network connection records.

        Processes records sequentially, building up the sequence buffer
        for each prediction.

        Args:
            records: List of record dictionaries.

        Returns:
            List of prediction result dictionaries.
        """
        logger.info(f"Batch prediction for {len(records)} records")
        results = []
        for record in records:
            result = self.predict_record(record)
            results.append(result)
        return results

    def predict_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Classify records from a pandas DataFrame.

        Args:
            df: DataFrame with UNSW-NB15 feature columns.

        Returns:
            Original DataFrame with added columns:
            - predicted_class
            - confidence
            - prob_Normal, prob_DoS, prob_Probe, prob_R2L, prob_U2R
        """
        logger.info(f"DataFrame prediction for {len(df)} records")

        # Reset buffer for fresh batch
        self._record_buffer = []

        predictions = []
        for _, row in df.iterrows():
            record = row.to_dict()
            result = self.predict_record(record)
            predictions.append(result)

        # Add prediction columns to DataFrame
        result_df = df.copy()
        result_df["predicted_class"] = [p["predicted_class"] for p in predictions]
        result_df["confidence"] = [p["confidence"] for p in predictions]

        class_labels = self.preprocessor.target_encoder.classes_
        for class_name in class_labels:
            result_df[f"prob_{class_name}"] = [
                p["all_probabilities"][class_name] for p in predictions
            ]

        return result_df

    def reset_buffer(self) -> None:
        """Clear the internal record buffer. Call between unrelated prediction sessions."""
        self._record_buffer = []
        logger.debug("Record buffer cleared.")

    def get_model_info(self) -> dict:
        """
        Get model metadata.

        Returns:
            Dictionary with model information loaded from saved metadata.
        """
        import json

        if os.path.exists(config.MODEL_METADATA_PATH):
            with open(config.MODEL_METADATA_PATH, "r") as f:
                return json.load(f)
        return {
            "model_name": "CNN_LSTM_Attention_IDS",
            "status": "metadata file not found",
        }
