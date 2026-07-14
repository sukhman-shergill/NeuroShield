"""
Sequence builder for CNN-LSTM input.

Converts flat feature arrays into overlapping sequences using a sliding window.
Each sequence represents a group of consecutive network connections,
allowing the LSTM to learn temporal attack patterns.
"""

import numpy as np
from tensorflow.keras.utils import to_categorical

import config
from utils.logger import get_logger

logger = get_logger(__name__)


def build_sequences(
    X: np.ndarray,
    y: np.ndarray,
    sequence_length: int = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build overlapping sequences from flat feature arrays using a sliding window.

    For input X with shape (N, features), produces sequences of shape
    (N - seq_len + 1, seq_len, features). Each sequence's label is the label
    of the last record in that window (the record we are predicting).

    Args:
        X: Feature array of shape (num_samples, num_features).
        y: Label array of shape (num_samples,) with integer class labels.
        sequence_length: Number of consecutive records per sequence.
            Defaults to config.SEQUENCE_LENGTH.

    Returns:
        Tuple of (X_seq, y_seq):
            X_seq: shape (num_sequences, sequence_length, num_features)
            y_seq: shape (num_sequences, num_classes) one-hot encoded
    """
    if sequence_length is None:
        sequence_length = config.SEQUENCE_LENGTH

    num_samples, num_features = X.shape

    if num_samples < sequence_length:
        raise ValueError(
            f"Not enough samples ({num_samples}) to build sequences "
            f"of length {sequence_length}"
        )

    num_sequences = num_samples - sequence_length + 1

    logger.info(
        f"Building sequences: {num_samples} records -> "
        f"{num_sequences} sequences of length {sequence_length}"
    )

    # Pre-allocate arrays for efficiency
    X_seq = np.empty((num_sequences, sequence_length, num_features), dtype=np.float32)
    y_seq_raw = np.empty(num_sequences, dtype=y.dtype)

    for i in range(num_sequences):
        X_seq[i] = X[i : i + sequence_length]
        # Label = the last record in the window (the one being classified)
        y_seq_raw[i] = y[i + sequence_length - 1]

    # One-hot encode the labels
    y_seq = to_categorical(y_seq_raw, num_classes=config.NUM_CLASSES)

    logger.info(f"Sequence shapes -> X: {X_seq.shape}, y: {y_seq.shape}")

    return X_seq, y_seq


def build_single_sequence(
    X: np.ndarray,
    sequence_length: int = None,
) -> np.ndarray:
    """
    Build a single sequence from a flat feature array for inference.

    Takes the last `sequence_length` records from X and reshapes into
    (1, sequence_length, features) for model input.

    Args:
        X: Feature array of shape (num_records, num_features).
        sequence_length: Number of records in the sequence.

    Returns:
        Array of shape (1, sequence_length, num_features).
    """
    if sequence_length is None:
        sequence_length = config.SEQUENCE_LENGTH

    if len(X) < sequence_length:
        # Pad with zeros at the beginning if we don't have enough records
        padding = np.zeros(
            (sequence_length - len(X), X.shape[1]), dtype=np.float32
        )
        X = np.vstack([padding, X])
        logger.debug(f"Padded sequence to length {sequence_length}")

    # Take the last sequence_length records
    sequence = X[-sequence_length:]
    return sequence.reshape(1, sequence_length, -1)
