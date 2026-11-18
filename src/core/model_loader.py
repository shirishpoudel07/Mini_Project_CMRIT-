import os
from src.core.config import MODEL_PATH

def load_medical_model():
    """Loads the trained Keras CNN model from medical_model.h5 with graceful fallback."""
    try:
        import tensorflow as tf
        if MODEL_PATH.exists():
            return tf.keras.models.load_model(str(MODEL_PATH))
    except Exception as e:
        print(f"[Model Loader Notice] Neural model fallback enabled: {e}")
    return None
