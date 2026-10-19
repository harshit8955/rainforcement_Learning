from app import create_app


def test_pages_and_health():
    app = create_app({"TESTING": True, "MAX_CONTENT_LENGTH": 50 * 1024 * 1024, "MAX_UPLOAD_BYTES": 10 * 1024 * 1024, "MAX_BATCH_SIZE": 10, "INFERENCE_API_URL": "", "INFERENCE_API_KEY": "", "INFERENCE_TIMEOUT_SECONDS": 1, "DATABASE_URL": "", "FEEDBACK_DIR": "instance/test-feedback"})
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/classifier").status_code == 200
    assert client.get("/css/style.css").status_code == 200
    health = client.get("/api/health")
    assert health.status_code == 503
    assert health.json["inference"]["configured"] is False
    assert "INFERENCE_API_URL" in health.json["inference"]["error"]


def test_missing_inference_is_explicit():
    app = create_app({"TESTING": True, "MAX_CONTENT_LENGTH": 50 * 1024 * 1024, "MAX_UPLOAD_BYTES": 10 * 1024 * 1024, "MAX_BATCH_SIZE": 10, "INFERENCE_API_URL": "", "INFERENCE_API_KEY": "", "INFERENCE_TIMEOUT_SECONDS": 1, "DATABASE_URL": "", "FEEDBACK_DIR": "instance/test-feedback"})
    response = app.test_client().post("/api/predict")
    assert response.status_code == 400


def test_feedback_requires_prediction_id():
    app = create_app({"TESTING": True, "MAX_CONTENT_LENGTH": 50 * 1024 * 1024, "MAX_UPLOAD_BYTES": 10 * 1024 * 1024, "MAX_BATCH_SIZE": 10, "INFERENCE_API_URL": "", "INFERENCE_API_KEY": "", "INFERENCE_TIMEOUT_SECONDS": 1, "DATABASE_URL": "", "FEEDBACK_DIR": "instance/test-feedback"})
    response = app.test_client().post("/api/feedback", json={"label": "cat"})
    assert response.status_code == 400
