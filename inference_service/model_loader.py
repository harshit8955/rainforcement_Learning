import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

_model = None


def get_model():
    global _model
    if _model is None:
        model_path = os.getenv("MODEL_PATH", str(Path(__file__).parent / "model.keras"))
        if not Path(model_path).exists():
            raise RuntimeError("Model artifact is not configured.")
        try:
            import tensorflow as tf
        except ImportError as exc:
            raise RuntimeError("TensorFlow is not installed.") from exc
        _model = _TensorFlowModel(tf.keras.models.load_model(model_path))
    return _model


class _TensorFlowModel:
    def __init__(self, model):
        self.model = model
        names_path = os.getenv("CLASS_NAMES_PATH", str(Path(__file__).parent / "class_names.json"))
        with open(names_path, encoding="utf-8") as file:
            names = json.load(file)
        self.class_names = [name.rstrip("s").lower() for name in names]
        if set(self.class_names) != {"cat", "dog"}:
            raise RuntimeError("CLASS_NAMES_PATH must contain cat and dog labels.")

    def predict(self, image):
        import tensorflow as tf
        array = np.asarray(image.resize((224, 224)), dtype=np.float32)
        array = tf.keras.applications.mobilenet_v2.preprocess_input(array)
        score = float(self.model.predict(array[None, ...], verbose=0).reshape(-1)[0])
        probabilities = {
            self.class_names[1]: score,
            self.class_names[0]: 1 - score,
        }
        label = max(probabilities, key=probabilities.get)
        return {
            "label": label,
            "confidence": probabilities[label],
            "probabilities": probabilities,
            "model_version": os.getenv("MODEL_VERSION", "mobilenetv2-cats-dogs-v1"),
        }
