"""
Data preprocessor for the NSL-KDD dataset.

Handles:
- Drop constant noise features
- Log transform skewed features (duration, src_bytes, dst_bytes)
- Label encoding of categorical features (protocol_type, service, flag)
- Standard scaling of numeric features
- Saving/loading fitted transformers for inference
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
    """Preprocesses raw NSL-KDD DataFrames into model-ready numeric arrays."""

    def __init__(self):
        self.label_encoders: dict[str, LabelEncoder] = {}
        self.scaler = StandardScaler()
        self.target_encoder = LabelEncoder()
        self._is_fitted = False

    def fit_transform(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, val_size: float = 0.15
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        train = train_df.copy()
        test = test_df.copy()

        # Drop constant features
        constant_cols = ["num_outbound_cmds"]
        train = train.drop(columns=[c for c in constant_cols if c in train.columns], errors="ignore")
        test = test.drop(columns=[c for c in constant_cols if c in test.columns], errors="ignore")

        # Log transform skewed features
        skewed_cols = ["duration", "src_bytes", "dst_bytes"]
        for col in skewed_cols:
            if col in train.columns:
                train[col] = np.log1p(train[col].values.astype(np.float32))
                test[col] = np.log1p(test[col].values.astype(np.float32))

        # Encode categorical features
        for col in config.CATEGORICAL_FEATURES:
            le = LabelEncoder()
            all_values = pd.concat([train[col], test[col]]).unique()
            le.fit(all_values)
            train[col] = le.transform(train[col])
            test[col] = le.transform(test[col])
            self.label_encoders[col] = le

        # Encode target labels
        self.target_encoder.fit(config.CLASS_NAMES)
        train_labels = train["attack_category"].values
        test_labels = test["attack_category"].values
        y_train = self.target_encoder.transform(train_labels)
        y_test = self.target_encoder.transform(test_labels)

        # Extract features
        drop_cols = ["label", "attack_category"]
        feature_cols = [c for c in train.columns if c not in drop_cols]
        X_train = train[feature_cols].values.astype(np.float32)
        X_test = test[feature_cols].values.astype(np.float32)

        # Split train and validation splits to prevent validation leakage
        from sklearn.model_selection import train_test_split
        X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(
            X_train, y_train, test_size=val_size, random_state=42, stratify=y_train
        )

        # Scale features (fit only on the training split)
        self.scaler.fit(X_train_split)
        X_train_split = self.scaler.transform(X_train_split)
        X_val_split = self.scaler.transform(X_val_split)
        X_test = self.scaler.transform(X_test)

        # Apply RandomOverSampler to handle class imbalance on the training split
        from imblearn.over_sampling import RandomOverSampler
        
        # Calculate dynamic target sampling strategy to oversample minority classes
        # to 30% of the majority class count
        unique_classes, class_counts = np.unique(y_train_split, return_counts=True)
        majority_class_count = max(class_counts)
        target_count = int(majority_class_count * 0.3)
        
        sampling_strategy = {}
        for cls, count in zip(unique_classes, class_counts):
            if count < target_count:
                sampling_strategy[int(cls)] = target_count
            else:
                sampling_strategy[int(cls)] = count
                
        logger.info(f"Oversampling target strategy: {sampling_strategy}")
        ros = RandomOverSampler(sampling_strategy=sampling_strategy, random_state=42)
        X_train_resampled, y_train_resampled = ros.fit_resample(X_train_split, y_train_split)
        
        # Shuffle training split
        shuffle_idx = np.random.RandomState(42).permutation(len(X_train_resampled))
        X_train_resampled = X_train_resampled[shuffle_idx]
        y_train_resampled = y_train_resampled[shuffle_idx]

        self._is_fitted = True
        return X_train_resampled, y_train_resampled, X_val_split, y_val_split, X_test, y_test

    def transform_single(self, record: dict) -> np.ndarray:
        """
        Transform a single raw record dict into a scaled feature vector.
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor not fitted. Call load_transformers() first.")

        # Build a single-row DataFrame
        df = pd.DataFrame([record])

        # Drop constant features
        constant_cols = ["num_outbound_cmds"]
        df = df.drop(columns=[c for c in constant_cols if c in df.columns], errors="ignore")

        # Log transform skewed features
        skewed_cols = ["duration", "src_bytes", "dst_bytes"]
        for col in skewed_cols:
            if col in df.columns:
                df[col] = np.log1p(df[col].values.astype(np.float32))

        # Encode categorical features
        for col in config.CATEGORICAL_FEATURES:
            if col in df.columns:
                le = self.label_encoders[col]
                known_classes = set(le.classes_)
                df[col] = df[col].apply(
                    lambda x: le.transform([x])[0] if x in known_classes else -1
                )

        # Drop non-feature columns if present
        drop_cols = ["label", "attack_category", "difficulty_level", "source_ip", "dest_ip"]
        feature_cols = [c for c in df.columns if c not in drop_cols]
        features = df[feature_cols].values.astype(np.float32)

        # Scale
        features = self.scaler.transform(features)
        return features[0]

    def transform_df(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """
        Transform an entire DataFrame using loaded transformers.
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor not loaded. Call load_transformers() first.")

        temp_df = df.copy()

        # Drop constant features
        constant_cols = ["num_outbound_cmds"]
        temp_df = temp_df.drop(columns=[c for c in constant_cols if c in temp_df.columns], errors="ignore")

        # Log transform skewed features
        skewed_cols = ["duration", "src_bytes", "dst_bytes"]
        for col in skewed_cols:
            if col in temp_df.columns:
                temp_df[col] = np.log1p(temp_df[col].values.astype(np.float32))

        # Encode categorical features
        for col in config.CATEGORICAL_FEATURES:
            if col in temp_df.columns:
                le = self.label_encoders[col]
                known_classes = set(le.classes_)
                temp_df[col] = temp_df[col].apply(
                    lambda x: le.transform([x])[0] if x in known_classes else -1
                )

        # Encode targets
        y = np.zeros(len(temp_df), dtype=np.int32)
        if "attack_category" in temp_df.columns:
            y = self.target_encoder.transform(temp_df["attack_category"].values)

        # Extract features and scale
        drop_cols = ["label", "attack_category", "difficulty_level", "source_ip", "dest_ip"]
        feature_cols = [c for c in temp_df.columns if c not in drop_cols]
        X = temp_df[feature_cols].values.astype(np.float32)
        X = self.scaler.transform(X)

        return X, y

    def save_transformers(self) -> None:
        if not self._is_fitted:
            raise RuntimeError("Nothing to save. Preprocessor not fitted yet.")
        joblib.dump(self.scaler, config.SCALER_SAVE_PATH)
        encoders_data = {
            "label_encoders": self.label_encoders,
            "target_encoder": self.target_encoder,
        }
        joblib.dump(encoders_data, config.LABEL_ENCODERS_SAVE_PATH)

    def load_transformers(self) -> None:
        if not os.path.exists(config.SCALER_SAVE_PATH):
            raise FileNotFoundError(f"Scaler not found at {config.SCALER_SAVE_PATH}")
        if not os.path.exists(config.LABEL_ENCODERS_SAVE_PATH):
            raise FileNotFoundError(f"Encoders not found at {config.LABEL_ENCODERS_SAVE_PATH}")

        self.scaler = joblib.load(config.SCALER_SAVE_PATH)
        encoders_data = joblib.load(config.LABEL_ENCODERS_SAVE_PATH)
        self.label_encoders = encoders_data["label_encoders"]
        self.target_encoder = encoders_data["target_encoder"]
        self._is_fitted = True
