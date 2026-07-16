"""
Data preprocessor optimized for the UNSW-NB15 dataset.

Pipeline:
  1. Log-transform skewed features (dur, sbytes, dbytes, rate, sload, dload, etc.)
  2. Label-encode categorical features (proto, service, state)
  3. Fit StandardScaler on training features, then scale both train and test.
"""

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class DataPreprocessor:
    """
    Preprocesses raw UNSW-NB15 DataFrames into model-ready arrays.
    """

    def __init__(self):
        self.label_encoders: dict[str, LabelEncoder] = {}
        self.scaler = StandardScaler()
        self.target_encoder = LabelEncoder()
        self._is_fitted = False

    def fit_transform(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Fit the preprocessor on training data and transform train and test sets chronologically.
        """
        train = train_df.copy()
        test  = test_df.copy()

        # 1. Log-transform skewed features
        for col in config.SKEWED_COLS:
            if col in train.columns:
                train[col] = np.log1p(train[col].values.astype(np.float32))
                test[col]  = np.log1p(test[col].values.astype(np.float32))

        # 2. Encode categorical features
        for col in config.CATEGORICAL_FEATURES:
            if col not in train.columns:
                continue
            le = LabelEncoder()
            all_values = pd.concat([train[col], test[col]]).astype(str).unique()
            le.fit(all_values)
            train[col] = le.transform(train[col].astype(str))
            test[col]  = le.transform(test[col].astype(str))
            self.label_encoders[col] = le

        # 3. Encode target labels
        self.target_encoder.fit(config.CLASS_NAMES)
        y_train = self.target_encoder.transform(
            train["attack_category"].values
        )
        y_test = self.target_encoder.transform(
            test["attack_category"].values
        )

        # 4. Extract feature matrices
        drop_cols  = ["label", "attack_category"]
        feat_cols  = [c for c in train.columns if c not in drop_cols]
        X_train = train[feat_cols].values.astype(np.float32)
        X_test       = test[feat_cols].values.astype(np.float32)

        # 5. Fit scaler on training set ONLY (no leakage)
        self.scaler.fit(X_train)
        X_train = self.scaler.transform(X_train)
        X_test  = self.scaler.transform(X_test)

        self._is_fitted = True

        from collections import Counter
        train_dist = Counter(y_train)
        logger.info("Training flat class distribution:")
        for cls_idx, cls_name in enumerate(config.CLASS_NAMES):
            count = train_dist.get(cls_idx, 0)
            logger.info(f"  {cls_name:8s}: {count:6d} samples")

        logger.info(f"Preprocessor fit complete → train: {X_train.shape}, test: {X_test.shape}")
        return X_train, y_train, X_test, y_test

    def transform_single(self, record: dict) -> np.ndarray:
        """
        Transform a single raw record dict into a scaled feature vector.
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor not fitted. Call load_transformers() first.")

        df = pd.DataFrame([record])

        # Drop constant / metadata columns
        drop_meta = ["label", "attack_category", "source_ip", "dest_ip", "id", "attack_cat"]
        df = df.drop(columns=[c for c in drop_meta if c in df.columns], errors="ignore")

        # Log-transform skewed features
        for col in config.SKEWED_COLS:
            if col in df.columns:
                df[col] = np.log1p(df[col].values.astype(np.float32))

        # Encode categoricals
        for col in config.CATEGORICAL_FEATURES:
            if col in df.columns and col in self.label_encoders:
                le = self.label_encoders[col]
                known = set(le.classes_)
                df[col] = df[col].astype(str).apply(
                    lambda x: le.transform([x])[0] if x in known else -1
                )

        features = df.values.astype(np.float32)
        return self.scaler.transform(features)[0]

    def transform_df(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """
        Transform an entire DataFrame using loaded transformers.
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor not loaded. Call load_transformers() first.")

        temp = df.copy()

        drop_meta = ["id", "attack_cat"]
        temp = temp.drop(columns=[c for c in drop_meta if c in temp.columns], errors="ignore")

        # Log-transform skewed features
        for col in config.SKEWED_COLS:
            if col in temp.columns:
                temp[col] = np.log1p(temp[col].values.astype(np.float32))

        # Encode categoricals
        for col in config.CATEGORICAL_FEATURES:
            if col in temp.columns and col in self.label_encoders:
                le = self.label_encoders[col]
                known = set(le.classes_)
                temp[col] = temp[col].astype(str).apply(
                    lambda x: le.transform([x])[0] if x in known else -1
                )

        # Encode target labels
        y = np.zeros(len(temp), dtype=np.int32)
        if "attack_category" in temp.columns:
            y = self.target_encoder.transform(temp["attack_category"].values)

        # Extract features and scale
        drop_cols  = ["label", "attack_category", "source_ip", "dest_ip"]
        feat_cols  = [c for c in temp.columns if c not in drop_cols]
        X = temp[feat_cols].values.astype(np.float32)
        X = self.scaler.transform(X)

        return X, y

    def save_transformers(self) -> None:
        """Persist scaler and encoders to disk."""
        if not self._is_fitted:
            raise RuntimeError("Nothing to save. Preprocessor not fitted yet.")
        joblib.dump(self.scaler, config.SCALER_SAVE_PATH)
        joblib.dump(
            {
                "label_encoders":  self.label_encoders,
                "target_encoder":  self.target_encoder,
                "dataset":         "unsw-nb15",
                "categorical_features": config.CATEGORICAL_FEATURES,
                "skewed_cols":     config.SKEWED_COLS,
                "constant_cols":   [],
            },
            config.LABEL_ENCODERS_SAVE_PATH,
        )
        logger.info("Preprocessor transformers saved successfully.")

    def load_transformers(self) -> None:
        """Restore scaler and encoders from disk."""
        if not os.path.exists(config.SCALER_SAVE_PATH):
            raise FileNotFoundError(f"Scaler not found at {config.SCALER_SAVE_PATH}")
        if not os.path.exists(config.LABEL_ENCODERS_SAVE_PATH):
            raise FileNotFoundError(f"Encoders not found at {config.LABEL_ENCODERS_SAVE_PATH}")

        self.scaler = joblib.load(config.SCALER_SAVE_PATH)
        data = joblib.load(config.LABEL_ENCODERS_SAVE_PATH)

        self.label_encoders  = data["label_encoders"]
        self.target_encoder  = data["target_encoder"]
        self._is_fitted = True
        logger.info("Preprocessor transformers loaded successfully.")
