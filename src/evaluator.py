"""
Model evaluator for the CNN-LSTM intrusion detection model.

Generates:
- Classification report (precision, recall, F1 per class)
- Confusion matrix (raw and normalized)
- ROC-AUC curves (one-vs-rest)
- All metrics saved as JSON for dashboard integration
"""

import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_curve,
    auc,
    accuracy_score,
    f1_score,
)

import config
from utils.logger import get_logger

logger = get_logger(__name__)


def evaluate_model(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> dict:
    """
    Evaluate the trained model on test data and generate all metrics and plots.

    Args:
        model: Trained Keras model.
        X_test: Test sequences, shape (num_samples, seq_len, features).
        y_test: One-hot test labels, shape (num_samples, num_classes).

    Returns:
        Dictionary containing all evaluation metrics.
    """
    logger.info("=" * 60)
    logger.info("EVALUATING MODEL")
    logger.info("=" * 60)

    # Get predictions
    y_pred_proba = model.predict(X_test, batch_size=config.BATCH_SIZE, verbose=1)
    y_pred = np.argmax(y_pred_proba, axis=1)
    y_true = np.argmax(y_test, axis=1)

    # --- Classification Report ---
    report = classification_report(
        y_true, y_pred,
        target_names=config.CLASS_NAMES,
        output_dict=True,
    )
    report_text = classification_report(
        y_true, y_pred,
        target_names=config.CLASS_NAMES,
    )

    logger.info(f"\n{report_text}")

    overall_accuracy = accuracy_score(y_true, y_pred)
    overall_f1 = f1_score(y_true, y_pred, average="weighted")
    logger.info(f"Overall Accuracy: {overall_accuracy:.4f}")
    logger.info(f"Weighted F1 Score: {overall_f1:.4f}")

    # Save classification report as JSON
    report["overall_accuracy"] = overall_accuracy
    report["weighted_f1"] = overall_f1

    with open(config.CLASSIFICATION_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Classification report saved to {config.CLASSIFICATION_REPORT_PATH}")

    # --- Confusion Matrix ---
    _plot_confusion_matrix(y_true, y_pred)

    # --- ROC Curves ---
    _plot_roc_curves(y_true, y_test, y_pred_proba)

    # --- Attack Distribution ---
    _plot_attack_distribution(y_true, y_pred)

    return report


def _plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> None:
    """Generate and save confusion matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred)

    # Normalized confusion matrix
    cm_normalized = cm.astype("float") / cm.sum(axis=1, keepdims=True)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Raw counts
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=config.CLASS_NAMES,
        yticklabels=config.CLASS_NAMES,
        ax=axes[0],
    )
    axes[0].set_title("Confusion Matrix (Counts)", fontsize=14)
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("Actual")

    # Normalized
    sns.heatmap(
        cm_normalized, annot=True, fmt=".2f", cmap="Blues",
        xticklabels=config.CLASS_NAMES,
        yticklabels=config.CLASS_NAMES,
        ax=axes[1],
    )
    axes[1].set_title("Confusion Matrix (Normalized)", fontsize=14)
    axes[1].set_xlabel("Predicted")
    axes[1].set_ylabel("Actual")

    plt.tight_layout()
    plt.savefig(config.CONFUSION_MATRIX_PATH, dpi=150, bbox_inches="tight")
    plt.close()

    # Also save as JSON for dashboard
    cm_json_path = config.CONFUSION_MATRIX_PATH.replace(".png", ".json")
    cm_data = {
        "matrix": cm.tolist(),
        "normalized_matrix": cm_normalized.tolist(),
        "labels": config.CLASS_NAMES,
    }
    with open(cm_json_path, "w") as f:
        json.dump(cm_data, f, indent=2)

    logger.info(f"Confusion matrix saved to {config.CONFUSION_MATRIX_PATH}")


def _plot_roc_curves(
    y_true: np.ndarray,
    y_test_one_hot: np.ndarray,
    y_pred_proba: np.ndarray,
) -> None:
    """Generate and save one-vs-rest ROC curves for each class."""
    fig, ax = plt.subplots(figsize=(10, 8))

    roc_data = {}

    for i, class_name in enumerate(config.CLASS_NAMES):
        # Check if this class exists in test data
        if y_test_one_hot[:, i].sum() == 0:
            logger.warning(f"No test samples for class '{class_name}', skipping ROC")
            continue

        fpr, tpr, _ = roc_curve(y_test_one_hot[:, i], y_pred_proba[:, i])
        roc_auc = auc(fpr, tpr)

        ax.plot(fpr, tpr, linewidth=2, label=f"{class_name} (AUC = {roc_auc:.3f})")

        roc_data[class_name] = {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "auc": float(roc_auc),
        }

    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random Classifier")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title("ROC Curves (One-vs-Rest)", fontsize=14)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(config.ROC_CURVES_PATH, dpi=150, bbox_inches="tight")
    plt.close()

    # Save ROC data as JSON for dashboard
    roc_json_path = config.ROC_CURVES_PATH.replace(".png", ".json")
    with open(roc_json_path, "w") as f:
        json.dump(roc_data, f, indent=2)

    logger.info(f"ROC curves saved to {config.ROC_CURVES_PATH}")


def _plot_attack_distribution(y_true: np.ndarray, y_pred: np.ndarray) -> None:
    """Generate and save attack distribution comparison chart."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # True distribution
    true_counts = np.bincount(y_true, minlength=config.NUM_CLASSES)
    pred_counts = np.bincount(y_pred, minlength=config.NUM_CLASSES)

    colors = ["#2ecc71", "#e74c3c", "#3498db", "#f39c12", "#9b59b6"]

    axes[0].bar(config.CLASS_NAMES, true_counts, color=colors)
    axes[0].set_title("Actual Attack Distribution", fontsize=14)
    axes[0].set_ylabel("Count")
    for i, v in enumerate(true_counts):
        axes[0].text(i, v + max(true_counts) * 0.01, str(v), ha="center", fontsize=9)

    axes[1].bar(config.CLASS_NAMES, pred_counts, color=colors)
    axes[1].set_title("Predicted Attack Distribution", fontsize=14)
    axes[1].set_ylabel("Count")
    for i, v in enumerate(pred_counts):
        axes[1].text(i, v + max(pred_counts) * 0.01, str(v), ha="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(config.ATTACK_DISTRIBUTION_PATH, dpi=150, bbox_inches="tight")
    plt.close()

    # Save as JSON
    dist_json_path = config.ATTACK_DISTRIBUTION_PATH.replace(".png", ".json")
    dist_data = {
        "labels": config.CLASS_NAMES,
        "actual_counts": true_counts.tolist(),
        "predicted_counts": pred_counts.tolist(),
    }
    with open(dist_json_path, "w") as f:
        json.dump(dist_data, f, indent=2)

    logger.info(f"Attack distribution saved to {config.ATTACK_DISTRIBUTION_PATH}")
