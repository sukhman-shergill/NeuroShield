import unittest
import numpy as np

import config
from src.sequence_builder import build_sequences, build_single_sequence


class TestSequenceBuilder(unittest.TestCase):
    def setUp(self):
        self.num_features = 40
        self.sequence_length = config.SEQUENCE_LENGTH
        
    def test_build_sequences(self):
        num_samples = 25
        X = np.random.randn(num_samples, self.num_features).astype(np.float32)
        y = np.random.randint(0, config.NUM_CLASSES, num_samples)
        
        X_seq, y_seq = build_sequences(X, y, sequence_length=self.sequence_length)
        
        expected_sequences = num_samples - self.sequence_length + 1
        
        self.assertEqual(X_seq.shape, (expected_sequences, self.sequence_length, self.num_features))
        self.assertEqual(y_seq.shape, (expected_sequences, config.NUM_CLASSES))
        
        # Verify sequence contents (sliding window)
        # First sequence should be X[0:seq_len]
        np.testing.assert_array_equal(X_seq[0], X[0:self.sequence_length])
        # Second sequence should be X[1:seq_len+1]
        np.testing.assert_array_equal(X_seq[1], X[1:self.sequence_length+1])
        
    def test_build_sequences_too_few_samples(self):
        # Sample count less than sequence length
        num_samples = self.sequence_length - 1
        X = np.random.randn(num_samples, self.num_features).astype(np.float32)
        y = np.random.randint(0, config.NUM_CLASSES, num_samples)
        
        with self.assertRaises(ValueError):
            build_sequences(X, y, sequence_length=self.sequence_length)
            
    def test_build_single_sequence(self):
        # Case 1: More samples than sequence length
        num_samples = 15
        X = np.random.randn(num_samples, self.num_features).astype(np.float32)
        seq = build_single_sequence(X, sequence_length=self.sequence_length)
        
        self.assertEqual(seq.shape, (1, self.sequence_length, self.num_features))
        # It should take the last sequence_length records
        np.testing.assert_array_equal(seq[0], X[-self.sequence_length:])
        
    def test_build_single_sequence_padding(self):
        # Case 2: Fewer samples than sequence length (should pad with zeros)
        num_samples = 5
        X = np.random.randn(num_samples, self.num_features).astype(np.float32)
        seq = build_single_sequence(X, sequence_length=self.sequence_length)
        
        self.assertEqual(seq.shape, (1, self.sequence_length, self.num_features))
        # The first (seq_len - num_samples) rows should be all zeros
        padding_len = self.sequence_length - num_samples
        self.assertTrue(np.all(seq[0, :padding_len] == 0))
        # The remaining rows should match X
        np.testing.assert_array_equal(seq[0, padding_len:], X)


if __name__ == "__main__":
    unittest.main()
