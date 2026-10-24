import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "development-only-change-me")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_REQUEST_BYTES", 50 * 1024 * 1024))
    MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", 10))
    INFERENCE_API_URL = os.getenv("INFERENCE_API_URL", "").rstrip("/")
    INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY", "")
    INFERENCE_TIMEOUT_SECONDS = float(os.getenv("INFERENCE_TIMEOUT_SECONDS", "30"))
    OOD_CONFIDENCE_THRESHOLD = float(os.getenv("OOD_CONFIDENCE_THRESHOLD", "0.62"))
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    FEEDBACK_DIR = os.getenv("FEEDBACK_DIR", "instance/feedback")
