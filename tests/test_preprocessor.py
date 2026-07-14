import unittest
import numpy as np
import pandas as pd
import os
import shutil

import config
from src.preprocessor import DataPreprocessor


class TestDataPreprocessor(unittest.TestCase):
    def setUp(self):
        self.preprocessor = DataPreprocessor()
        
        # Build a synthetic DataFrame matching NSL-KDD schema
        # We need all columns in config.COLUMN_NAMES
        np.random.seed(42)
        num_samples = 100
        
        data = {}
        for col in config.COLUMN_NAMES:
            if col in config.CATEGORICAL_FEATURES:
                if col == "protocol_type":
                    data[col] = np.random.choice(["tcp", "udp", "icmp"], num_samples)
                elif col == "service":
                    data[col] = np.random.choice(["http", "ftp", "smtp"], num_samples)
                elif col == "flag":
                    data[col] = np.random.choice(["SF", "S0", "REJ"], num_samples)
            elif col == "label":
                data[col] = np.random.choice(["normal", "neptune", "satan"], num_samples)
            elif col == "difficulty_level":
                data[col] = np.random.randint(0, 22, num_samples)
            elif col in ["duration", "src_bytes", "dst_bytes"]:
                data[col] = np.random.exponential(100, num_samples)
            else:
                data[col] = np.random.randn(num_samples)
                
        self.df = pd.DataFrame(data)
        # Ensure balanced classes: exactly 20 of each of the 5 classes
        self.df["attack_category"] = np.tile(config.CLASS_NAMES, 20)
        self.df = self.df.drop(columns=["difficulty_level"], errors="ignore")
        
    def test_fit_transform(self):
        # Split into dummy train and test (80 train, 20 test)
        train_df = self.df.iloc[:80].copy()
        test_df = self.df.iloc[80:].copy()
        
        X_train, y_train, X_val, y_val, X_test, y_test = self.preprocessor.fit_transform(train_df, test_df, val_size=0.25)
        
        expected_features_count = len(config.COLUMN_NAMES) - 3
        
        # Since it oversamples, the resampled training set should have balanced/larger shapes
        self.assertEqual(X_train.shape[1], expected_features_count)
        self.assertEqual(X_val.shape[0], 20)  # 25% of 80 is 20
        self.assertEqual(X_val.shape[1], expected_features_count)
        self.assertEqual(X_test.shape[0], 20)
        self.assertEqual(X_test.shape[1], expected_features_count)
        self.assertEqual(len(y_train), len(X_train))
        
    def test_transform_single(self):
        # Fit preprocessor
        self.preprocessor.fit_transform(self.df, self.df)
        
        # Take a single record as dict
        record = self.df.iloc[0].to_dict()
        record["source_ip"] = "192.168.1.100"
        record["dest_ip"] = "10.0.0.1"
        
        features = self.preprocessor.transform_single(record)
        expected_features_count = len(config.COLUMN_NAMES) - 3
        
        self.assertEqual(features.shape[0], expected_features_count)
        self.assertTrue(np.all(np.isfinite(features)))
        
    def test_transform_df(self):
        # Fit preprocessor
        self.preprocessor.fit_transform(self.df, self.df)
        
        # Transform a dataframe
        X, y = self.preprocessor.transform_df(self.df)
        expected_features_count = len(config.COLUMN_NAMES) - 3
        
        self.assertEqual(X.shape[0], len(self.df))
        self.assertEqual(X.shape[1], expected_features_count)
        self.assertEqual(y.shape[0], len(self.df))


if __name__ == "__main__":
    unittest.main()
