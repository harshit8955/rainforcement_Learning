"""Add approved anonymous feedback to the training set and retrain a new model.

This is deliberately an explicit command. User uploads never replace the
production model automatically.
"""
import argparse
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="instance/visionai.db")
    parser.add_argument("--dataset", type=Path, default=Path("dataset"))
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inference_service"),
        help="Directory for the model loaded by the inference service.",
    )
    args = parser.parse_args()

    with sqlite3.connect(args.database) as connection:
        rows = connection.execute(
            "SELECT id, image_path, feedback_label FROM predictions "
            "WHERE feedback_label IN ('cat', 'dog') AND image_path IS NOT NULL"
        ).fetchall()
    if not rows:
        raise SystemExit("No labeled feedback is available for retraining.")

    imported = 0
    for prediction_id, image_path, label in rows:
        source = Path(image_path)
        if not source.exists():
            continue
        destination = args.dataset / "train" / f"{label}s" / f"feedback_{prediction_id}.jpg"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source).convert("RGB") as image:
            image.save(destination, format="JPEG", quality=92)
        imported += 1
    if not imported:
        raise SystemExit("Feedback records exist, but their stored images are missing.")

    subprocess.run(
        [
            sys.executable,
            "training/train.py",
            "--dataset",
            str(args.dataset),
            "--epochs",
            str(args.epochs),
            "--output",
            str(args.output),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
