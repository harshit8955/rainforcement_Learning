import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class HistoryStore:
    def __init__(self, database_url, feedback_dir="instance/feedback"):
        self.database_url = database_url
        self.enabled = bool(database_url)
        self.path = database_url.removeprefix("sqlite:///") if database_url.startswith("sqlite:///") else ""
        self.feedback_dir = Path(feedback_dir)
        if self.path:
            self.enabled = True
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.path) as connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY, filename TEXT, label TEXT, confidence REAL, model_version TEXT, created_at TEXT)"
                )
                columns = {row[1] for row in connection.execute("PRAGMA table_info(predictions)")}
                if "feedback_label" not in columns:
                    connection.execute("ALTER TABLE predictions ADD COLUMN feedback_label TEXT")
                if "feedback_at" not in columns:
                    connection.execute("ALTER TABLE predictions ADD COLUMN feedback_at TEXT")
                if "image_path" not in columns:
                    connection.execute("ALTER TABLE predictions ADD COLUMN image_path TEXT")

    def status(self):
        return {"configured": self.enabled, "persistent": self.enabled}

    def save(self, result, filename, image=None):
        if not self.path:
            return None
        image_path = None
        if image is not None:
            self.feedback_dir.mkdir(parents=True, exist_ok=True)
            image_path = str(self.feedback_dir / f"{uuid4().hex}.bin")
            image.stream.seek(0)
            with open(image_path, "wb") as stored:
                stored.write(image.stream.read())
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                "INSERT INTO predictions (filename, label, confidence, model_version, created_at, image_path) VALUES (?, ?, ?, ?, ?, ?)",
                (filename, result.get("label"), result.get("confidence"), result.get("model_version"), datetime.now(timezone.utc).isoformat(), image_path),
            )
            return cursor.lastrowid

    def save_feedback(self, prediction_id, feedback_label):
        if not self.path:
            raise LookupError("Feedback storage is not configured.")
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                "UPDATE predictions SET feedback_label = ?, feedback_at = ? WHERE id = ?",
                (feedback_label, datetime.now(timezone.utc).isoformat(), prediction_id),
            )
            if cursor.rowcount == 0:
                raise LookupError("Prediction was not found.")

    def list_recent(self):
        if not self.path:
            return []
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 100")]

    def clear(self):
        if self.path:
            with sqlite3.connect(self.path) as connection:
                connection.execute("DELETE FROM predictions")
