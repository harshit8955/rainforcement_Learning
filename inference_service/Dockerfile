FROM python:3.12-slim

WORKDIR /service
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /service/inference_service/

ENV MODEL_PATH=/service/inference_service/model.keras
ENV CLASS_NAMES_PATH=/service/inference_service/class_names.json
ENV PORT=8000

CMD gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 2 --timeout 120 inference_service.app:app
