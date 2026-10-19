import os
import time
from io import BytesIO

from flask import Flask, jsonify, request
from PIL import Image, UnidentifiedImageError

from .model_loader import get_model

app = Flask(__name__)
MAX_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
CLASS_NAMES = ["cat", "dog"]


def authorized():
    configured = os.getenv("INFERENCE_API_KEY", "")
    return not configured or request.headers.get("Authorization") == "Bearer " + configured


@app.get("/health")
def health():
    try:
        get_model()
        return jsonify({"ready": True, "model_version": os.getenv("MODEL_VERSION", "mobilenetv2-cats-dogs-v1")})
    except RuntimeError as exc:
        return jsonify({"ready": False, "error": str(exc)}), 503


@app.post("/predict")
def predict():
    if not authorized():
        return jsonify({"success": False, "error": "Unauthorized."}), 401
    uploaded = request.files.get("image")
    if not uploaded:
        return jsonify({"success": False, "error": "Image is required."}), 400
    content = uploaded.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        return jsonify({"success": False, "error": "Image is too large."}), 413
    try:
        image = Image.open(BytesIO(content)).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return jsonify({"success": False, "error": "Invalid image."}), 400
    started = time.perf_counter()
    prediction = get_model().predict(image)
    prediction["inference_ms"] = round((time.perf_counter() - started) * 1000)
    return jsonify({"success": True, "prediction": prediction})

