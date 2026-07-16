"""
Dataset loader for UNSW-NB15 dataset.

Processes the UNSW-NB15 dataset (modern, realistic network traffic).
Maps the raw 9 attack categories into a clean 5-class schema:
Normal, DoS, Probe, R2L, U2R.
"""

import os
import pandas as pd

import config
from utils.logger import get_logger

logger = get_logger(__name__)


def map_attack_label(attack_cat: str) -> str:
    """
    Map a UNSW-NB15 attack category to the 5-class schema.

    UNSW-NB15 has 9 attack types: DoS, Fuzzers, Analysis, Backdoors,
    Exploits, Generic, Reconnaissance, Shellcode, Worms.

    Args:
        attack_cat: Raw UNSW-NB15 attack_cat value (e.g., 'Shellcode').

    Returns:
        One of: Normal, DoS, Probe, R2L, U2R.
    """
    cat = str(attack_cat).strip()
    if not cat or cat.lower() in ("nan", "none", ""):
        return "Normal"
    mapped = config.ATTACK_MAPPING.get(cat)
    if mapped is None:
        logger.warning(f"Unknown UNSW-NB15 category '{cat}', mapping to 'Normal'")
        return "Normal"
    return mapped


def load_unsw_file(file_path: str) -> pd.DataFrame:
    """
    Load and parse a UNSW-NB15 CSV file.

    Args:
        file_path: Path to the UNSW-NB15 CSV file.

    Returns:
        DataFrame with 'attack_category' column and UNSW-NB15 features.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"UNSW-NB15 file not found: {file_path}\n"
            "Download the dataset from Kaggle or UNSW Canberra and place the CSV files in data/raw/"
        )

    logger.info(f"Loading UNSW-NB15 from {file_path}")
    df = pd.read_csv(file_path, low_memory=False)

    # Normalize column names to lowercase
    df.columns = df.columns.str.strip().str.lower()

    # Map attack_cat → 5-class attack_category
    if "attack_cat" in df.columns:
        df["attack_category"] = df["attack_cat"].apply(map_attack_label)
    elif "label" in df.columns:
        df["attack_category"] = df["label"].apply(
            lambda x: "Normal" if int(x) == 0 else "DoS"
        )
        logger.warning("attack_cat column not found; using binary label (DoS only)")
    else:
        raise ValueError("UNSW-NB15 CSV must have 'attack_cat' or 'label' column")

    # Drop metadata columns not used as features
    drop_cols = ["id", "label", "attack_cat"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    # Keep only known feature columns + attack_category
    feature_cols = [c for c in config.FEATURE_NAMES if c in df.columns]
    missing = [c for c in config.FEATURE_NAMES if c not in df.columns]
    if missing:
        logger.warning(f"UNSW-NB15 missing expected columns: {missing}")

    df = df[feature_cols + ["attack_category"]]
    df = df.fillna(0)

    logger.info(f"Loaded {len(df)} UNSW-NB15 records ({len(feature_cols)} features)")
    logger.info(f"Class distribution:\n{df['attack_category'].value_counts().to_string()}")
    return df


def load_train_test() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load train and test DataFrames for the UNSW-NB15 dataset.

    Returns:
        Tuple of (train_df, test_df).
    """
    return load_unsw_file(config.TRAIN_FILE), load_unsw_file(config.TEST_FILE)
