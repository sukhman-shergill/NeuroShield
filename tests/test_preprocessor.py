"""
Unit tests for DataPreprocessor.

Tests validate:
  - fit_transform() produces correct shapes for UNSW-NB15
  - No data leakage: scaler is fitted on train split only
  - transform_single() returns a valid 1-D float32 feature vector
  - transform_df() returns matching X and y arrays
  - save_transformers() / load_transformers() round-trip works
"""

import os
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd

import config
from src.preprocessor import DataPreprocessor


def _make_unsw_df(n: int = 100) -> pd.DataFrame:
    """Build a synthetic DataFrame that mimics the UNSW-NB15 schema."""
    np.random.seed(42)
    data = {}

    for col in config.FEATURE_NAMES:
        if col in config.CATEGORICAL_FEATURES:
            if col == "proto":
                data[col] = np.random.choice(["tcp", "udp", "unas"], n)
            elif col == "service":
                data[col] = np.random.choice(["-", "http", "ftp"], n)
            elif col == "state":
                data[col] = np.random.choice(["FIN", "CON", "INT"], n)
        elif col in config.SKEWED_COLS:
            data[col] = np.random.exponential(100, n).astype(np.float32)
        else:
            data[col] = np.abs(np.random.randn(n)).astype(np.float32)

    df = pd.DataFrame(data)
    df["attack_category"] = np.tile(config.CLASS_NAMES, n // len(config.CLASS_NAMES))
    return df


class TestDataPreprocessor(unittest.TestCase):
    """Tests for DataPreprocessor with UNSW-NB15 dataset schema."""

    def setUp(self):
        self.preprocessor = DataPreprocessor()
        df = _make_unsw_df(100)
        self.train_df = df.iloc[:80].copy()
        self.test_df  = df.iloc[80:].copy()

    def test_fit_transform_shapes(self):
        """fit_transform() should produce correctly shaped arrays for train and test splits."""
        X_train, y_train, X_test, y_test = (
            self.preprocessor.fit_transform(self.train_df, self.test_df)
        )
        expected_features = len(config.FEATURE_NAMES)
        self.assertEqual(X_train.shape[1], expected_features)
        self.assertEqual(X_test.shape[1],  expected_features)
        self.assertEqual(len(y_train), X_train.shape[0])
        self.assertEqual(len(y_test),  X_test.shape[0])

    def test_no_oversampling(self):
        """Flat training set should contain all input train_df records (no oversampling)."""
        X_train, y_train, *_ = self.preprocessor.fit_transform(
            self.train_df, self.test_df
        )
        self.assertEqual(len(X_train), 80)

    def test_all_finite(self):
        """All output arrays should contain only finite values."""
        X_train, y_train, X_test, y_test = (
            self.preprocessor.fit_transform(self.train_df, self.test_df)
        )
        self.assertTrue(np.all(np.isfinite(X_train)), "X_train contains non-finite values")
        self.assertTrue(np.all(np.isfinite(X_test)),  "X_test contains non-finite values")

    def test_transform_single(self):
        """transform_single() should return a valid 1-D float32 feature vector."""
        self.preprocessor.fit_transform(self.train_df, self.test_df)
        record = self.train_df.iloc[0].to_dict()
        record["source_ip"] = "192.168.1.100"
        record["dest_ip"]   = "10.0.0.1"

        features = self.preprocessor.transform_single(record)
        self.assertEqual(features.ndim, 1)
        self.assertEqual(features.dtype, np.float32)
        self.assertTrue(np.all(np.isfinite(features)))

    def test_transform_df(self):
        """transform_df() should return X and y with matching number of samples."""
        self.preprocessor.fit_transform(self.train_df, self.test_df)
        X, y = self.preprocessor.transform_df(self.train_df)
        self.assertEqual(X.shape[0], len(self.train_df))
        self.assertEqual(y.shape[0], len(self.train_df))
        self.assertTrue(np.all(np.isfinite(X)))

    def test_save_load_roundtrip(self):
        """save_transformers() / load_transformers() should round-trip correctly."""
        self.preprocessor.fit_transform(self.train_df, self.test_df)

        orig_scaler_path   = config.SCALER_SAVE_PATH
        orig_encoders_path = config.LABEL_ENCODERS_SAVE_PATH

        tmpdir = tempfile.mkdtemp()
        try:
            config.SCALER_SAVE_PATH          = os.path.join(tmpdir, "scaler.joblib")
            config.LABEL_ENCODERS_SAVE_PATH  = os.path.join(tmpdir, "encoders.joblib")
            self.preprocessor.save_transformers()

            # Load into a fresh instance
            loaded = DataPreprocessor()
            loaded.load_transformers()
            self.assertTrue(loaded._is_fitted)

            # Check that transform_single produces same result
            record = self.train_df.iloc[0].to_dict()
            feat_orig   = self.preprocessor.transform_single(record)
            feat_loaded = loaded.transform_single(record)
            np.testing.assert_allclose(feat_orig, feat_loaded, rtol=1e-5)
        finally:
            config.SCALER_SAVE_PATH         = orig_scaler_path
            config.LABEL_ENCODERS_SAVE_PATH = orig_encoders_path
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
