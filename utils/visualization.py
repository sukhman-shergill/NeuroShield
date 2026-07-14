"""
Visualization utilities for generating dashboard-ready charts and data.

All plots are saved as PNG files. All data is also saved as JSON
for easy integration with any frontend dashboard framework.
"""

import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

import config
from utils.logger import get_logger

logger = get_logger(__name__)


def plot_training_history(history_path: str = None) -> None:
    """
    Plot training and validation loss/accuracy curves.

    Args:
        history_path: Path to training_history.json.
            Defaults to config.TRAINING_HISTORY_PATH.
    """
    if history_path is None:
        history_path = config.TRAINING_HISTORY_PATH

    if not os.path.exists(history_path):
        logger.warning(f"Training history not found at {history_path}")
        return

    with open(history_path, "r") as f:
        history = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    epochs = range(1, len(history["loss"]) + 1)

    # Loss curve
    axes[0].plot(epochs, history["loss"], "b-", linewidth=2, label="Training Loss")
    if "val_loss" in history:
        axes[0].plot(epochs, history["val_loss"], "r-", linewidth=2, label="Validation Loss")
    axes[0].set_title("Model Loss", fontsize=14)
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # Accuracy curve
    axes[1].plot(epochs, history["accuracy"], "b-", linewidth=2, label="Training Accuracy")
    if "val_accuracy" in history:
        axes[1].plot(
            epochs, history["val_accuracy"], "r-", linewidth=2, label="Validation Accuracy"
        )
    axes[1].set_title("Model Accuracy", fontsize=14)
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(config.TRAINING_CURVES_PATH, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"Training curves saved to {config.TRAINING_CURVES_PATH}")


def plot_per_class_metrics(report_path: str = None) -> None:
    """
    Plot per-class precision, recall, and F1 as grouped bar charts.

    Args:
        report_path: Path to classification_report.json.
            Defaults to config.CLASSIFICATION_REPORT_PATH.
    """
    if report_path is None:
        report_path = config.CLASSIFICATION_REPORT_PATH

    if not os.path.exists(report_path):
        logger.warning(f"Classification report not found at {report_path}")
        return

    with open(report_path, "r") as f:
        report = json.load(f)

    # Extract per-class metrics
    classes = config.CLASS_NAMES
    precision = [report.get(c, {}).get("precision", 0) for c in classes]
    recall = [report.get(c, {}).get("recall", 0) for c in classes]
    f1 = [report.get(c, {}).get("f1-score", 0) for c in classes]

    x = np.arange(len(classes))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))

    bars1 = ax.bar(x - width, precision, width, label="Precision", color="#3498db")
    bars2 = ax.bar(x, recall, width, label="Recall", color="#2ecc71")
    bars3 = ax.bar(x + width, f1, width, label="F1-Score", color="#e74c3c")

    ax.set_xlabel("Attack Category", fontsize=12)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Per-Class Classification Metrics", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(classes, fontsize=11)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.15)
    ax.grid(axis="y", alpha=0.3)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0, height + 0.02,
                f"{height:.2f}", ha="center", va="bottom", fontsize=8,
            )

    plt.tight_layout()
    metrics_path = os.path.join(config.OUTPUTS_DIR, "per_class_metrics.png")
    plt.savefig(metrics_path, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"Per-class metrics chart saved to {metrics_path}")


def plot_attention_weights(
    attention_weights: np.ndarray,
    sample_indices: list = None,
    save_path: str = None,
) -> None:
    """
    Visualize attention weights for selected samples.

    Shows which time steps the model focuses on for its predictions.

    Args:
        attention_weights: Array of shape (num_samples, time_steps, 1).
        sample_indices: List of sample indices to plot. Defaults to first 5.
        save_path: Path to save the plot.
    """
    if save_path is None:
        save_path = os.path.join(config.OUTPUTS_DIR, "attention_weights.png")

    if sample_indices is None:
        sample_indices = list(range(min(5, len(attention_weights))))

    num_samples = len(sample_indices)
    fig, axes = plt.subplots(num_samples, 1, figsize=(12, 3 * num_samples))

    if num_samples == 1:
        axes = [axes]

    for idx, sample_idx in enumerate(sample_indices):
        weights = attention_weights[sample_idx].flatten()
        time_steps = range(1, len(weights) + 1)

        axes[idx].bar(time_steps, weights, color="#3498db", alpha=0.8)
        axes[idx].set_xlabel("Time Step")
        axes[idx].set_ylabel("Attention Weight")
        axes[idx].set_title(f"Sample {sample_idx}: Attention Distribution")
        axes[idx].set_xticks(time_steps)
        axes[idx].grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

    # Save as JSON
    json_path = save_path.replace(".png", ".json")
    data = {
        str(idx): attention_weights[idx].flatten().tolist()
        for idx in sample_indices
    }
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Attention weights visualization saved to {save_path}")


def generate_all_visualizations() -> None:
    """Generate all available visualization plots from saved data."""
    logger.info("Generating all visualizations...")
    plot_training_history()
    plot_per_class_metrics()
    logger.info("All visualizations generated.")
