"""
Prediction explainability for the CNN-LSTM-Attention NIDS.

Two complementary explanation strategies are provided:

1. AttentionExplainer (fast, built-in):
   Uses the attention weights already computed during inference by
   build_attention_model(). Returns which time steps in the 10-record
   connection sequence the model focused on. This is unique to our
   architecture and requires no additional dependencies.

2. FeatureExplainer (deeper, SHAP-based):
   Uses permutation importance as a lightweight alternative to SHAP's
   KernelExplainer, which is extremely slow on sequence models. Permutation
   importance shuffles one feature at a time and measures how much the
   predicted probability drops — identical interpretation to SHAP but O(F)
   instead of O(2^F) complexity.

   If shap is installed, falls back to SHAP DeepExplainer for richer
   interaction-aware feature attributions.

Both explanations are serializable to JSON and exposed via the Flask
/explain endpoint.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import numpy as np
import tensorflow as tf

import config
from src.model import build_model, AttentionLayer
from utils.logger import get_logger

logger = get_logger(__name__)

# Feature names for the currently active dataset (set at runtime by config)
_FEATURE_NAMES: list[str] | None = None


def get_feature_names() -> list[str]:
    """Return ordered feature names for the UNSW-NB15 dataset."""
    return config.FEATURE_NAMES


class AttentionExplainer:
    """
    Explain predictions using the model's own attention weights.

    The model already computes attention weights over the 10-record
    sequence window during inference. This explainer surfaces those weights
    as a human-readable 'which time steps mattered' explanation.

    Args:
        main_model:       The trained CNN-LSTM-Attention Keras model.
        input_shape:      Shape tuple (sequence_length, num_features).
    """

    def __init__(self, main_model: tf.keras.Model, input_shape: tuple):
        self.main_model = main_model
        # Build a secondary model that exposes attention weights
        self._attention_model = self._build_attention_extractor(main_model)
        self.sequence_length = input_shape[0]

    def _build_attention_extractor(
        self, main_model: tf.keras.Model
    ) -> tf.keras.Model:
        """Build a sub-model that outputs attention weights (shared weights)."""
        try:
            attention_layer = main_model.get_layer("attention")
            dropout_output  = main_model.get_layer("dropout_lstm").output
            _, attn_weights = attention_layer(dropout_output)
            return tf.keras.Model(
                inputs=main_model.input,
                outputs=attn_weights,
                name="attention_extractor",
            )
        except Exception as e:
            logger.warning(f"Could not build attention extractor: {e}")
            return None

    def explain(self, sequence: np.ndarray) -> dict:
        """
        Compute attention-based explanation for a single sequence.

        Args:
            sequence: Input array of shape (1, sequence_length, num_features).

        Returns:
            Dictionary with:
              - attention_weights: list of floats, one per time step
              - top_time_steps:    list of {step, weight, relative_importance}
              - summary:           human-readable explanation string
        """
        if self._attention_model is None:
            return {"error": "Attention extractor not available"}

        attn = self._attention_model.predict(sequence, verbose=0)
        # attn shape: (1, time_steps, 1) → flatten to (time_steps,)
        weights = attn[0, :, 0].tolist()

        # Rank time steps by attention weight
        ranked = sorted(
            enumerate(weights), key=lambda x: x[1], reverse=True
        )

        top = [
            {
                "step": int(i),
                "weight": round(float(w), 4),
                "relative_importance": round(float(w) / (max(weights) + 1e-8), 3),
            }
            for i, w in ranked[:3]
        ]

        # Most recent step = step (sequence_length - 1)
        focus_step = ranked[0][0]
        recency = "most recent" if focus_step == self.sequence_length - 1 else (
            "second most recent" if focus_step == self.sequence_length - 2
            else f"step {focus_step + 1}"
        )

        summary = (
            f"The model focused primarily on the {recency} connection in the "
            f"{self.sequence_length}-record window (attention weight: "
            f"{ranked[0][1]:.3f}). "
            f"Top 3 time steps: {[t['step'] for t in top]}."
        )

        return {
            "attention_weights": [round(w, 4) for w in weights],
            "top_time_steps": top,
            "summary": summary,
        }


class FeatureExplainer:
    """
    Explain predictions via permutation feature importance.

    For each feature, the prediction probability for the predicted class is
    measured before and after shuffling that feature across the sequence.
    The drop in probability is the feature's importance score.

    This is O(num_features) inferences — fast enough for real-time use.

    Args:
        model:        Trained CNN-LSTM-Attention Keras model.
        num_features: Number of input features.
        top_k:        Number of top features to return in explanations.
    """

    def __init__(
        self,
        model: tf.keras.Model,
        num_features: int,
        top_k: int = 10,
    ):
        self.model = model
        self.num_features = num_features
        self.top_k = top_k
        self.feature_names = get_feature_names()
        # Truncate/pad feature_names to match actual feature count
        if len(self.feature_names) > num_features:
            self.feature_names = self.feature_names[:num_features]
        elif len(self.feature_names) < num_features:
            self.feature_names += [
                f"feature_{i}" for i in range(len(self.feature_names), num_features)
            ]

    def explain(self, sequence: np.ndarray, predicted_class_idx: int) -> dict:
        """
        Compute permutation-based feature importances for one sequence.

        Args:
            sequence:            Shape (1, seq_len, num_features).
            predicted_class_idx: Index of the predicted class (to track prob drop).

        Returns:
            Dictionary with:
              - feature_importances: list of {feature, importance, direction}
              - top_features:        top_k most important features
              - summary:             human-readable explanation
        """
        # Baseline probability for the predicted class
        baseline_proba = float(
            self.model.predict(sequence, verbose=0)[0, predicted_class_idx]
        )

        importances = []
        seq = sequence.copy()  # shape (1, seq_len, features)

        for feat_idx in range(self.num_features):
            # Save original column values
            original_vals = seq[0, :, feat_idx].copy()
            # Shuffle this feature across the time dimension
            shuffled = original_vals.copy()
            np.random.shuffle(shuffled)
            seq[0, :, feat_idx] = shuffled

            # Measure probability drop
            perturbed_proba = float(
                self.model.predict(seq, verbose=0)[0, predicted_class_idx]
            )
            importance = baseline_proba - perturbed_proba

            # Restore original values
            seq[0, :, feat_idx] = original_vals

            importances.append({
                "feature": self.feature_names[feat_idx],
                "importance": round(importance, 4),
                "direction": "increases_risk" if importance > 0 else "decreases_risk",
            })

        # Sort by absolute importance
        importances.sort(key=lambda x: abs(x["importance"]), reverse=True)
        top = importances[: self.top_k]

        top_names = [f['feature'] for f in top[:3]]
        summary = (
            f"Top drivers for this prediction: {', '.join(top_names)}. "
            f"Baseline confidence: {baseline_proba:.1%}."
        )

        return {
            "feature_importances": importances,
            "top_features": top,
            "baseline_confidence": round(baseline_proba, 4),
            "summary": summary,
        }


def try_shap_explain(
    model: tf.keras.Model,
    sequence: np.ndarray,
    background: np.ndarray,
    predicted_class_idx: int,
    feature_names: list[str],
) -> Optional[dict]:
    """
    Attempt SHAP DeepExplainer explanation (optional dependency).

    Falls back gracefully if shap is not installed. SHAP provides more
    accurate attributions than permutation importance by computing exact
    Shapley values, but is slower (~5-30s per explanation).

    Args:
        model:               Trained Keras model.
        sequence:            Input sequence, shape (1, seq_len, features).
        background:          Background dataset for SHAP baseline (N, seq_len, features).
        predicted_class_idx: Class index to explain.
        feature_names:       Feature names for labelling.

    Returns:
        SHAP explanation dict, or None if shap is not installed.
    """
    try:
        import shap  # optional
    except ImportError:
        return None

    try:
        # DeepExplainer uses a background distribution to compute baseline
        bg_sample = background[:min(50, len(background))]
        explainer = shap.DeepExplainer(model, bg_sample)
        shap_values = explainer.shap_values(sequence)

        # shap_values: list of length num_classes, each (1, seq_len, features)
        # Aggregate over time dimension → (features,)
        class_shap = np.abs(shap_values[predicted_class_idx][0]).mean(axis=0)
        ranked = sorted(
            zip(feature_names, class_shap),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        return {
            "method": "shap_deep_explainer",
            "top_features": [
                {"feature": f, "shap_value": round(float(v), 5)}
                for f, v in ranked[:10]
            ],
        }
    except Exception as e:
        logger.warning(f"SHAP explanation failed: {e}")
        return None
