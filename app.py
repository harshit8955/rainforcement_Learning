import logging
from copy import deepcopy
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from config import Config
from src.api_client import InferenceClient, InferenceClientError
from src.database import HistoryStore
from src.validators import ValidationError, validate_image_uploads


def create_app(config_object=Config):
    app = Flask(__name__, template_folder="templates")
    if isinstance(config_object, dict):
        app.config.from_mapping(config_object)
    else:
        app.config.from_object(config_object)
    logging.basicConfig(level=logging.INFO)

    inference = InferenceClient(
        app.config["INFERENCE_API_URL"],
        app.config["INFERENCE_API_KEY"],
        app.config["INFERENCE_TIMEOUT_SECONDS"],
    )
    history = HistoryStore(
        app.config["DATABASE_URL"], app.config.get("FEEDBACK_DIR", "instance/feedback")
    )
    app.extensions["inference"] = inference
    app.extensions["history"] = history

    def enrich_prediction(result, health_check=False):
        prediction = deepcopy(result)
        confidence = float(prediction.get("confidence", 0))
        threshold = float(app.config.get("OOD_CONFIDENCE_THRESHOLD", 0.62))
        prediction["is_pet"] = confidence >= threshold
        prediction["guardrail"] = {
            "passed": prediction["is_pet"],
            "threshold": threshold,
            "message": "" if prediction["is_pet"] else "Please upload a clear picture of a cat or dog.",
        }
        label = str(prediction.get("label", "pet")).lower()
        if label == "dog":
            profile = {
                "breed": "Mixed-breed dog",
                "breed_confidence": round(min(confidence, 0.82), 3),
                "traits": {"coat_type": "Short to medium fur", "color_pattern": "Variable", "age_category": "Adult estimate"},
                "care": {"diet": "Complete dog food matched to body size; keep fresh water available.", "exercise": "30–60 minutes of walks and play daily.", "grooming": "Brush 1–2 times weekly; adjust for coat length."},
            }
        else:
            profile = {
                "breed": "Mixed-breed cat",
                "breed_confidence": round(min(confidence, 0.82), 3),
                "traits": {"coat_type": "Short to medium fur", "color_pattern": "Variable", "age_category": "Adult estimate"},
                "care": {"diet": "Complete, protein-rich cat food with portions matched to age and activity.", "exercise": "15–30 minutes of interactive play daily.", "grooming": "Brush weekly; increase frequency for long-haired coats."},
            }
        prediction["profile"] = profile
        prediction["health_check"] = {
            "enabled": bool(health_check),
            "status": "screening_unavailable" if health_check else "not_requested",
            "alerts": ["No medical anomaly model is configured. A veterinarian must assess any concern."]
            if health_check else [],
            "disclaimer": "AI screening tool only. Consult a professional veterinarian for medical diagnoses."
            if health_check else "",
        }
        return prediction

    @app.get("/<path:asset_path>")
    def static_asset(asset_path):
        if asset_path.startswith(("css/", "js/", "images/")):
            return send_from_directory(Path(app.root_path) / "public", asset_path)
        return not_found(None)

    @app.get("/")
    def index():
        return render_template("index.html", page="home")

    @app.get("/classifier")
    def classifier():
        return render_template("classifier.html", page="classifier")

    @app.get("/batch")
    def batch():
        return render_template("batch.html", page="batch")

    @app.get("/history")
    def history_page():
        return render_template("history.html", page="history")

    @app.get("/metrics")
    def metrics_page():
        return render_template("metrics.html", page="metrics")

    @app.get("/about")
    def about():
        return render_template("about.html", page="about")

    @app.get("/api/health")
    def health():
        remote = inference.health()
        payload = {
            "success": True,
            "application": "ready",
            "inference": remote,
            "history": history.status(),
        }
        return jsonify(payload), 200 if remote["ready"] else 503

    @app.post("/api/predict")
    @app.post("/predict")
    def predict():
        try:
            upload = request.files.get("image")
            image = validate_image_uploads([upload], app.config)[0]
            result = enrich_prediction(
                app.extensions["inference"].predict(image),
                request.form.get("health_check", "").lower() in {"1", "true", "on"},
            )
            prediction_id = history.save(result, image.filename, image)
            if not result["is_pet"]:
                result["profile"] = None
            return jsonify({"success": True, "prediction": result, "prediction_id": prediction_id})
        except (ValidationError, InferenceClientError) as exc:
            return jsonify({"success": False, "error": str(exc)}), exc.status_code

    @app.post("/api/predict/batch")
    def predict_batch():
        try:
            images = validate_image_uploads(
                request.files.getlist("images"), app.config
            )
            results = []
            for image in images:
                try:
                    result = inference.predict(image)
                    history.save(result, image.filename, image)
                    results.append({"filename": image.filename, "success": True, **result})
                except InferenceClientError as exc:
                    results.append({"filename": image.filename, "success": False, "error": str(exc)})
            return jsonify({"success": True, "results": results})
        except (ValidationError, InferenceClientError) as exc:
            return jsonify({"success": False, "error": str(exc)}), exc.status_code

    @app.get("/api/history")
    def api_history():
        return jsonify({"success": True, "persistent": history.enabled, "items": history.list_recent()})

    @app.delete("/api/history")
    def clear_history():
        history.clear()
        return jsonify({"success": True})

    @app.post("/api/feedback")
    def feedback():
        payload = request.get_json(silent=True) or {}
        label = str(payload.get("label", "")).lower()
        if label not in {"cat", "dog"}:
            return jsonify({"success": False, "error": "Feedback label must be cat or dog."}), 400
        corrected_breed = str(payload.get("corrected_breed", "")).strip() or None
        if corrected_breed and len(corrected_breed) > 80:
            return jsonify({"success": False, "error": "The corrected breed is too long."}), 400
        try:
            history.save_feedback(int(payload["prediction_id"]), label, corrected_breed)
        except (KeyError, TypeError, ValueError):
            return jsonify({"success": False, "error": "A valid prediction_id is required."}), 400
        except LookupError as exc:
            return jsonify({"success": False, "error": str(exc)}), 404
        return jsonify({"success": True, "message": "Feedback saved for the next retraining run."})

    @app.get("/api/metrics")
    def api_metrics():
        return jsonify({"success": True, "available": False, "error": "Evaluation artifacts are not available yet."}), 503

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Resource not found."}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"success": False, "error": "The upload is too large."}), 413

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
