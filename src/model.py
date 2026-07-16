"""
Hybrid CNN-LSTM-Attention model for network intrusion detection.

Architecture:
    Input (sequence_length, num_features)
      → Conv1D (64 filters, k=3) → BatchNorm → ReLU → SpatialDropout1D(0.2)
      → Conv1D (128 filters, k=3) → BatchNorm → ReLU → MaxPool1D(2)
      → SpatialDropout1D(0.2)
      → Bidirectional LSTM (128 units, return_sequences=True)
      → Dropout(0.2)
      → AttentionLayer  (Bahdanau-style learned attention)
      → Dense(128, relu)  → Dropout(0.2)
      → Dense(num_classes, softmax)

Loss:
    FocalLoss(gamma=2.0, alpha=sqr_class_weights, label_smoothing=0.05)
    Per-class alpha from square-root frequency scaling (Cui et al. 2019).
    Label smoothing prevents overconfident predictions on dominant classes.
    See src/losses.py for details.

Metrics:
    accuracy   — fast training signal
    MacroF1Score — class-balanced metric; drives EarlyStopping monitor.
      Macro F1 = mean(F1 per class), treating U2R equally with Normal.
"""

import tensorflow as tf
from tensorflow.keras import layers, Model

import config
from src.losses import FocalLoss
from src.metrics import MacroF1Score
from utils.logger import get_logger

logger = get_logger(__name__)


class AttentionLayer(layers.Layer):
    """
    Bahdanau-style additive attention over LSTM time steps.

    Learns to weight each time step in the connection sequence based on its
    relevance to the final classification. The resulting context vector
    summarises the entire sequence into a fixed-size representation,
    focusing on the most attack-indicative time steps.

    Interpretation:
      High attention weight at time step t means the connection record at
      position t in the 10-record window was the primary driver of the
      model's prediction. This is surfaced via the /explain/attention API
      endpoint for SOC analyst explainability.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self, input_shape):
        # input_shape: (batch_size, time_steps, features)
        feature_dim = input_shape[-1]

        self.W_attention = self.add_weight(
            name="attention_weight",
            shape=(feature_dim, feature_dim),
            initializer="glorot_uniform",
            trainable=True,
        )
        self.b_attention = self.add_weight(
            name="attention_bias",
            shape=(feature_dim,),
            initializer="zeros",
            trainable=True,
        )
        self.v_attention = self.add_weight(
            name="attention_vector",
            shape=(feature_dim, 1),
            initializer="glorot_uniform",
            trainable=True,
        )
        super().build(input_shape)

    def call(self, inputs):
        """
        Compute attention weights and apply them.

        Args:
            inputs: Tensor of shape (batch, time_steps, features).

        Returns:
            context:          Attention-weighted sum, shape (batch, features).
            attention_weights: The attention distribution, shape (batch, time_steps, 1).
        """
        # Score each time step: tanh(X @ W + b) @ v
        score = tf.nn.tanh(
            tf.tensordot(inputs, self.W_attention, axes=[[2], [0]]) + self.b_attention
        )
        attention_weights = tf.nn.softmax(
            tf.tensordot(score, self.v_attention, axes=[[2], [0]]), axis=1
        )

        # Weighted sum of inputs
        context = tf.reduce_sum(inputs * attention_weights, axis=1)
        return context, attention_weights

    def get_config(self):
        return super().get_config()


def build_model(input_shape: tuple, num_classes: int = None, class_weights: list = None) -> Model:
    """
    Build and compile the hybrid CNN-LSTM-Attention model.

    Args:
        input_shape: Shape of a single input sequence (sequence_length, num_features).
        num_classes: Number of output classes. Defaults to config.NUM_CLASSES.

    Returns:
        Compiled Keras Model with FocalLoss and MacroF1Score.
    """
    if num_classes is None:
        num_classes = config.NUM_CLASSES

    logger.info(f"Building model: input_shape={input_shape}, classes={num_classes}")

    inputs = layers.Input(shape=input_shape, name="input_sequence")
    l2_reg = tf.keras.regularizers.l2(config.L2_REGULARIZATION)

    # --- CNN Block: Extract local/spatial patterns from features ---

    x = layers.Conv1D(
        filters=config.CNN_FILTERS_1,
        kernel_size=config.CNN_KERNEL_SIZE_1,
        padding="same",
        kernel_regularizer=l2_reg,
        name="conv1d_1",
    )(inputs)
    x = layers.BatchNormalization(name="bn_1")(x)
    x = layers.Activation("relu", name="relu_1")(x)
    x = layers.SpatialDropout1D(0.2, name="spatial_dropout_1")(x)

    x = layers.Conv1D(
        filters=config.CNN_FILTERS_2,
        kernel_size=config.CNN_KERNEL_SIZE_2,
        padding="same",
        kernel_regularizer=l2_reg,
        name="conv1d_2",
    )(x)
    x = layers.BatchNormalization(name="bn_2")(x)
    x = layers.Activation("relu", name="relu_2")(x)
    x = layers.MaxPooling1D(pool_size=config.POOL_SIZE, name="maxpool")(x)
    x = layers.SpatialDropout1D(0.2, name="spatial_dropout_2")(x)

    # --- LSTM Block: Capture temporal dependencies ---

    x = layers.Bidirectional(
        layers.LSTM(config.LSTM_UNITS_1, return_sequences=True, name="lstm_1"),
        name="bilstm",
    )(x)
    x = layers.Dropout(config.DROPOUT_RATE, name="dropout_lstm")(x)

    # --- Attention Block: Focus on critical time steps ---
    context, _ = AttentionLayer(name="attention")(x)

    # --- Classification Head ---
    x = layers.Dense(
        config.DENSE_UNITS, activation="relu",
        kernel_regularizer=l2_reg, name="dense_1",
    )(context)
    x = layers.Dropout(config.DROPOUT_RATE, name="dropout_dense")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="output")(x)

    model = Model(inputs=inputs, outputs=outputs, name="CNN_LSTM_Attention_IDS")

    # Compile with Focal Loss + Macro F1 (class-balanced training signal)
    alpha = config.FOCAL_LOSS_ALPHA if class_weights is None else class_weights

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config.LEARNING_RATE),
        loss=FocalLoss(
            gamma=config.FOCAL_LOSS_GAMMA,
            alpha=alpha,
            label_smoothing=config.LABEL_SMOOTHING,
            name="focal_loss",
        ),
        metrics=[
            "accuracy",
            MacroF1Score(num_classes=num_classes, name="macro_f1"),
        ],
    )

    model.summary(print_fn=logger.info)
    logger.info("Model built and compiled with FocalLoss + MacroF1.")
    return model


def build_attention_model(input_shape: tuple, num_classes: int = None) -> tuple[Model, Model]:
    """
    Build the main model AND an attention-extraction sub-model.

    The attention sub-model shares weights with the main model but outputs
    attention weights for per-prediction explainability (via /explain/attention).

    Args:
        input_shape: Shape of input sequence (sequence_length, num_features).
        num_classes: Number of output classes.

    Returns:
        Tuple of (main_model, attention_model).
        attention_model outputs shape (batch, time_steps, 1).
    """
    main_model = build_model(input_shape, num_classes)

    attention_layer = main_model.get_layer("attention")
    bilstm_output   = main_model.get_layer("dropout_lstm").output
    _, attn_weights = attention_layer(bilstm_output)

    attention_model = Model(
        inputs=main_model.input,
        outputs=attn_weights,
        name="attention_extractor",
    )
    return main_model, attention_model
