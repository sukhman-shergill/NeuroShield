"""
Custom Keras metrics for imbalanced intrusion detection.

Why MacroF1 instead of accuracy:
  Accuracy is misleading on imbalanced datasets. A model that always predicts
  "Normal" on NSL-KDD achieves ~53% accuracy while detecting zero attacks.
  Macro F1 treats each class equally — a perfect score requires good performance
  on *all* classes including rare U2R (~52 samples) and R2L (~1005 samples).

  Macro F1 = mean(F1_class_0, F1_class_1, ..., F1_class_N)
  where each F1_class_i = 2 * precision_i * recall_i / (precision_i + recall_i)

Usage in model.compile():
  from src.metrics import MacroF1Score
  model.compile(
      ...,
      metrics=["accuracy", MacroF1Score(num_classes=5, name="macro_f1")]
  )

Usage in EarlyStopping:
  EarlyStopping(monitor="val_macro_f1", mode="max", patience=5)
"""

import tensorflow as tf


class MacroF1Score(tf.keras.metrics.Metric):
    """
    Macro-averaged F1 score computed from a running confusion matrix.

    Accumulates predictions across batches in a confusion matrix, then computes
    per-class precision, recall, and F1 at the end of each epoch.

    Args:
        num_classes: Total number of target classes.
        name:        Metric name for Keras tracking.
    """

    def __init__(self, num_classes: int, name: str = "macro_f1", **kwargs):
        super().__init__(name=name, **kwargs)
        self.num_classes = num_classes
        # Persistent confusion matrix accumulates across all batches in an epoch
        self.confusion_matrix = self.add_weight(
            name="confusion_matrix",
            shape=(num_classes, num_classes),
            initializer="zeros",
            dtype=tf.float32,
        )

    def update_state(
        self,
        y_true: tf.Tensor,
        y_pred: tf.Tensor,
        sample_weight=None,
    ) -> None:
        """
        Accumulate batch predictions into the running confusion matrix.

        Args:
            y_true: One-hot labels, shape (batch, num_classes).
            y_pred: Softmax probabilities, shape (batch, num_classes).
            sample_weight: Unused. Present for Keras API compatibility.
        """
        y_true_idx = tf.cast(tf.argmax(y_true, axis=-1), tf.int32)
        y_pred_idx = tf.cast(tf.argmax(y_pred, axis=-1), tf.int32)

        batch_cm = tf.math.confusion_matrix(
            y_true_idx, y_pred_idx,
            num_classes=self.num_classes,
            dtype=tf.float32,
        )
        self.confusion_matrix.assign_add(batch_cm)

    def result(self) -> tf.Tensor:
        """
        Compute macro F1 from the accumulated confusion matrix.

        Returns:
            Scalar macro-averaged F1 score in [0, 1].
        """
        cm = self.confusion_matrix
        # True positives: diagonal elements
        tp = tf.linalg.diag_part(cm)
        # False positives: column sums minus diagonal
        fp = tf.reduce_sum(cm, axis=0) - tp
        # False negatives: row sums minus diagonal
        fn = tf.reduce_sum(cm, axis=1) - tp

        # Per-class precision and recall (epsilon prevents division by zero)
        precision = tp / (tp + fp + 1e-7)
        recall    = tp / (tp + fn + 1e-7)

        # Per-class F1
        f1_per_class = 2.0 * precision * recall / (precision + recall + 1e-7)

        # Macro average: equal weight to all classes regardless of support
        return tf.reduce_mean(f1_per_class)

    def reset_state(self) -> None:
        """Reset confusion matrix at the start of each epoch."""
        self.confusion_matrix.assign(
            tf.zeros((self.num_classes, self.num_classes), dtype=tf.float32)
        )
