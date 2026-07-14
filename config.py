"""
Central configuration for the Hybrid CNN-LSTM Network Traffic Intelligence Engine.
All paths, hyperparameters, and settings are defined here.
"""

import os

# IMPORTANT: Set Keras backend to TensorFlow before any TF/Keras imports.
# Keras 3.x defaults to trying PyTorch first, which we don't need.
os.environ["KERAS_BACKEND"] = "tensorflow"

# ---------------------------------------------------------------------------
# Project root directory (auto-detected from this file's location)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Directory paths (auto-created at runtime)
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Create directories if they don't exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, OUTPUTS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ---------------------------------------------------------------------------
# NSL-KDD Dataset URLs and file names
# ---------------------------------------------------------------------------
DATASET_URLS = {
    "train": "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain%2B.txt",
    "test": "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest%2B.txt",
}

TRAIN_FILE = os.path.join(RAW_DATA_DIR, "KDDTrain+.txt")
TEST_FILE = os.path.join(RAW_DATA_DIR, "KDDTest+.txt")

# ---------------------------------------------------------------------------
# NSL-KDD column names (41 features + label + difficulty_level)
# ---------------------------------------------------------------------------
COLUMN_NAMES = [
    "duration", "protocol_type", "service", "flag", "src_bytes",
    "dst_bytes", "land", "wrong_fragment", "urgent", "hot",
    "num_failed_logins", "logged_in", "num_compromised", "root_shell",
    "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate", "label", "difficulty_level",
]

# Categorical feature columns (need encoding)
CATEGORICAL_FEATURES = ["protocol_type", "service", "flag"]

# ---------------------------------------------------------------------------
# Attack type mapping: specific attack name -> category
# ---------------------------------------------------------------------------
ATTACK_MAPPING = {
    # Normal
    "normal": "Normal",
    # DoS attacks
    "back": "DoS", "land": "DoS", "neptune": "DoS", "pod": "DoS",
    "smurf": "DoS", "teardrop": "DoS", "apache2": "DoS", "udpstorm": "DoS",
    "processtable": "DoS", "mailbomb": "DoS",
    # Probe attacks
    "ipsweep": "Probe", "nmap": "Probe", "portsweep": "Probe",
    "satan": "Probe", "mscan": "Probe", "saint": "Probe",
    # R2L attacks
    "ftp_write": "R2L", "guess_passwd": "R2L", "imap": "R2L",
    "multihop": "R2L", "phf": "R2L", "spy": "R2L", "warezclient": "R2L",
    "warezmaster": "R2L", "snmpgetattack": "R2L", "named": "R2L",
    "xlock": "R2L", "xsnoop": "R2L", "sendmail": "R2L",
    "httptunnel": "R2L", "worm": "R2L", "snmpguess": "R2L",
    # U2R attacks
    "buffer_overflow": "U2R", "loadmodule": "U2R", "perl": "U2R",
    "rootkit": "U2R", "xterm": "U2R", "ps": "U2R",
    "sqlattack": "U2R",
}

# Class label order (index = numeric label)
CLASS_NAMES = ["Normal", "DoS", "Probe", "R2L", "U2R"]
NUM_CLASSES = len(CLASS_NAMES)

# ---------------------------------------------------------------------------
# Sequence building parameters
# ---------------------------------------------------------------------------
SEQUENCE_LENGTH = 10  # Number of consecutive records per sequence

# ---------------------------------------------------------------------------
# Model hyperparameters
# ---------------------------------------------------------------------------
# CNN layers
CNN_FILTERS_1 = 64
CNN_KERNEL_SIZE_1 = 3
CNN_FILTERS_2 = 128
CNN_KERNEL_SIZE_2 = 3
POOL_SIZE = 2

# LSTM layers
LSTM_UNITS_1 = 128  # First BiLSTM layer
LSTM_UNITS_2 = 64   # Second LSTM layer

# Dense layers
DENSE_UNITS = 128
DROPOUT_RATE = 0.2  # Reduced from 0.4 to allow the model to learn better representations
L2_REGULARIZATION = 1e-5  # Reduced L2 penalty to prevent underfitting

# ---------------------------------------------------------------------------
# Training parameters
# ---------------------------------------------------------------------------
BATCH_SIZE = 256
EPOCHS = 30
LEARNING_RATE = 0.0005
EARLY_STOPPING_PATIENCE = 4
REDUCE_LR_PATIENCE = 3
REDUCE_LR_FACTOR = 0.5
VALIDATION_SPLIT = 0.15

# ---------------------------------------------------------------------------
# Saved model and artifact paths
# ---------------------------------------------------------------------------
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, "cnn_lstm_model.keras")
SCALER_SAVE_PATH = os.path.join(MODELS_DIR, "scaler.joblib")
LABEL_ENCODERS_SAVE_PATH = os.path.join(MODELS_DIR, "label_encoders.joblib")
TRAINING_HISTORY_PATH = os.path.join(OUTPUTS_DIR, "training_history.json")
CLASSIFICATION_REPORT_PATH = os.path.join(OUTPUTS_DIR, "classification_report.json")
CONFUSION_MATRIX_PATH = os.path.join(OUTPUTS_DIR, "confusion_matrix.png")
TRAINING_CURVES_PATH = os.path.join(OUTPUTS_DIR, "training_curves.png")
ROC_CURVES_PATH = os.path.join(OUTPUTS_DIR, "roc_curves.png")
ATTACK_DISTRIBUTION_PATH = os.path.join(OUTPUTS_DIR, "attack_distribution.png")
MODEL_METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

# ---------------------------------------------------------------------------
# API configuration
# ---------------------------------------------------------------------------
API_HOST = "0.0.0.0"
API_PORT = 5000
