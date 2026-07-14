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
        num_samples = 20
        
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
        self.df["attack_category"] = np.random.choice(config.CLASS_NAMES, num_samples)
        self.df = self.df.drop(columns=["difficulty_level"], errors="ignore")
        
    def test_fit_transform(self):
        # Split into dummy train and test
        train_df = self.df.iloc[:15].copy()
        test_df = self.df.iloc[15:].copy()
        
        X_train, y_train, X_test, y_test = self.preprocessor.fit_transform(train_df, test_df)
        
        # Assertions on shapes
        # We dropped 1 constant column (num_outbound_cmds)
        # We also drop label and attack_category during feature extraction
        expected_features_count = len(config.COLUMN_NAMES) - 3
        
        self.assertEqual(X_train.shape[0], 15)
        self.assertEqual(X_train.shape[1], expected_features_count)
        self.assertEqual(X_test.shape[0], 5)
        self.assertEqual(X_test.shape[1], expected_features_count)
        self.assertEqual(y_train.shape[0], 15)
        self.assertEqual(y_test.shape[0], 5)
        
    def test_transform_single(self):
        # We first need to fit the preprocessor
        self.preprocessor.fit_transform(self.df, self.df)
        
        # Take a single record as dict
        record = self.df.iloc[0].to_dict()
        # Add mock IP columns that the live system injects
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
