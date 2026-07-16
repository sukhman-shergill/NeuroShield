"""
Focal Loss for class-imbalanced multi-class classification.

Why Focal Loss instead of RandomOverSampling:
  RandomOverSampler duplicates flat records before sliding-window construction.
  Duplicated records then appear in adjacent windows, creating artificial
  temporal correlations that don't exist in real network traffic. Focal Loss
  solves the imbalance problem at the loss level, not the data level — no
  synthetic records are ever created.

Reference:
  Lin et al., "Focal Loss for Dense Object Detection" (RetinaNet, CVPR 2017)
  https://arxiv.org/abs/1708.02002

Formula:
  FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

  When p_t is high (model is confident / easy sample):
    (1 - p_t)^gamma → 0  ⟹  loss contribution is suppressed
  When p_t is low (model is uncertain / hard minority sample):
    (1 - p_t)^gamma → 1  ⟹  full loss is applied

  gamma=2.0 is the standard value from the original paper.
  alpha can be a scalar (uniform) or a list of per-class weights computed via
  square-root frequency scaling (Cui et al., CVPR 2019).

  label_smoothing (ε): Replaces hard one-hot targets with soft targets:
    y_smooth = y_true * (1 - ε) + ε / num_classes
  This prevents overconfident softmax predictions on dominant classes,
  improving calibration and minority-class recall.
"""

import tensorflow as tf


class FocalLoss(tf.keras.losses.Loss):
    """
    Multi-class focal loss with per-class alpha weighting and label smoothing.

    Args:
        gamma:           Focusing parameter. Higher values suppress easy examples more
                         aggressively. gamma=0 reduces to standard cross-entropy.
                         gamma=2.0 is the standard choice (Lin et al. 2017).
        alpha:           Balancing factor. Can be:
                           - A scalar float (e.g. 1.0): uniform weighting.
                           - A list of floats (len = num_classes): per-class weights
                             computed via square-root frequency scaling.
        label_smoothing: Smoothing factor ε ∈ [0, 1). Replaces hard one-hot targets
                         with soft targets to prevent overconfident predictions on
                         dominant classes. 0.0 disables smoothing. Default 0.05.
        name:            Loss name for Keras tracking.
    """

    def __init__(
        self,
        gamma: float = 2.0,
        alpha: float = 0.25,
        label_smoothing: float = 0.05,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.gamma = gamma
        self.label_smoothing = label_smoothing

        # Convert numpy arrays or tensors to plain Python types for JSON serialization
        if hasattr(alpha, "tolist"):
            alpha = alpha.tolist()
        elif hasattr(alpha, "numpy"):
            alpha = alpha.numpy().tolist()
        elif isinstance(alpha, (list, tuple)):
            alpha = [float(x) for x in alpha]
        else:
            alpha = float(alpha)

        self.alpha = alpha

    def call(self, y_true: tf.Tensor, y_pred: tf.Tensor) -> tf.Tensor:
        """
        Compute focal loss for a batch.

        Args:
            y_true: One-hot ground truth labels, shape (batch, num_classes).
            y_pred: Predicted probabilities from softmax, shape (batch, num_classes).

        Returns:
            Scalar mean loss for the batch.
        """
        # Clip predictions to prevent log(0)
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1.0 - 1e-7)

        # Apply label smoothing: spread probability mass from true class to all classes
        # y_smooth = y_true * (1 - ε) + ε / K
        # This prevents the model from collapsing to near-100% confidence on easy classes.
        if self.label_smoothing > 0.0:
            num_classes = tf.cast(tf.shape(y_true)[-1], tf.float32)
            y_true = y_true * (1.0 - self.label_smoothing) + (
                self.label_smoothing / num_classes
            )

        # Standard cross-entropy term: -y_true * log(y_pred)
        cross_entropy = -y_true * tf.math.log(y_pred)

        # p_t: probability of the correct class per sample → shape (batch, 1)
        # Uses un-smoothed y_pred vs smoothed y_true so focal weight reflects
        # the true class probability, not the smoothed target.
        p_t = tf.reduce_sum(y_true * y_pred, axis=-1, keepdims=True)

        # Per-class alpha weighting (vector or scalar)
        # If alpha is a list [w_DoS, w_Normal, w_Probe, w_R2L, w_U2R]:
        #   alpha_t = sum(y_true * alpha, axis=-1) → shape (batch, 1)
        # This selects the class weight of the true class for each sample.
        if isinstance(self.alpha, list):
            alpha_t = tf.reduce_sum(y_true * self.alpha, axis=-1, keepdims=True)
        else:
            alpha_t = self.alpha

        # Focal weight: alpha_t * (1 - p_t)^gamma
        focal_weight = alpha_t * tf.pow(1.0 - p_t, self.gamma)

        # Apply focal weight to per-class cross-entropy
        focal_loss = focal_weight * cross_entropy

        # Sum over classes, mean over batch
        return tf.reduce_mean(tf.reduce_sum(focal_loss, axis=-1))

    def get_config(self) -> dict:
        """Serialize config so the loss can be saved/loaded with the model."""
        return {
            **super().get_config(),
            "gamma": self.gamma,
            "alpha": self.alpha,
            "label_smoothing": self.label_smoothing,
        }
