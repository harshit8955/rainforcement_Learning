import logging
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
    def predict():
        try:
            upload = request.files.get("image")
            image = validate_image_uploads([upload], app.config)[0]
            result = inference.predict(image)
            prediction_id = history.save(result, image.filename, image)
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
        try:
            history.save_feedback(int(payload["prediction_id"]), label)
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
