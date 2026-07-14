"""
NSL-KDD dataset loader.

Downloads the NSL-KDD dataset from GitHub if not already present,
parses the raw text files, and maps attack labels to 5 categories:
Normal, DoS, Probe, R2L, U2R.
"""

import os

import pandas as pd
import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)


def download_file(url: str, save_path: str) -> None:
    """
    Download a file from a URL and save it to disk.

    Args:
        url: URL to download from.
        save_path: Local file path to save to.
    """
    if os.path.exists(save_path):
        logger.info(f"File already exists, skipping download: {save_path}")
        return

    logger.info(f"Downloading {url} ...")
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    with open(save_path, "wb") as f:
        f.write(response.content)

    logger.info(f"Saved to {save_path} ({len(response.content) / 1024:.1f} KB)")


def download_dataset() -> None:
    """Download train and test NSL-KDD files if not already present."""
    download_file(config.DATASET_URLS["train"], config.TRAIN_FILE)
    download_file(config.DATASET_URLS["test"], config.TEST_FILE)


def map_attack_label(label: str) -> str:
    """
    Map a specific attack name to its category.

    Args:
        label: The raw attack label from the dataset (e.g., 'neptune', 'normal').

    Returns:
        The attack category string (Normal, DoS, Probe, R2L, or U2R).
    """
    label_clean = label.strip().lower()
    category = config.ATTACK_MAPPING.get(label_clean)
    if category is None:
        logger.warning(f"Unknown attack label '{label}', mapping to 'Normal'")
        return "Normal"
    return category


def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load and parse a single NSL-KDD data file.

    The file is a CSV without headers. We assign column names from config,
    strip the trailing dot from labels, and map specific attacks to categories.

    Args:
        file_path: Path to the NSL-KDD text file.

    Returns:
        A pandas DataFrame with data.
    """
    logger.info(f"Loading dataset from {file_path}")

    df = pd.read_csv(file_path, header=None, names=config.COLUMN_NAMES)

    # Remove trailing dot from labels if present (some versions have 'normal.' instead of 'normal')
    df["label"] = df["label"].astype(str).str.strip().str.rstrip(".")

    # Map specific attack names to 5 categories
    df["attack_category"] = df["label"].apply(map_attack_label)

    # Drop the difficulty_level column (not needed for classification)
    df = df.drop(columns=["difficulty_level"], errors="ignore")

    logger.info(f"Loaded {len(df)} records with {df['attack_category'].nunique()} attack categories")
    logger.info(f"Class distribution:\n{df['attack_category'].value_counts().to_string()}")

    return df


def load_train_test() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Download (if needed) and load the train and test datasets.

    Returns:
        A tuple of (train_df, test_df) DataFrames.
    """
    download_dataset()
    train_df = load_dataset(config.TRAIN_FILE)
    test_df = load_dataset(config.TEST_FILE)
    return train_df, test_df

