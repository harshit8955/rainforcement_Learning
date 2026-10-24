# PetVision

PetVision is a Flask image-classification application for cat-versus-dog recognition. The responsive UI includes drag-and-drop uploads, image previews, confidence meters, OOD guardrails, a trait/care profile, optional health-triage messaging, and a feedback loop. Vercel hosts the Flask UI and API gateway, while a separate Python service hosts TensorFlow and the trained MobileNetV2 model.

## Architecture

```text
Browser -> Flask on Vercel -> HTTPS inference service -> MobileNetV2
                                      |
                                      +-> PostgreSQL or local SQLite history
```

The web application does not invent predictions. When `INFERENCE_API_URL` is missing, prediction requests return an explicit configuration error.

## Feedback learning

After a prediction, a user can confirm whether the image is a cat or dog. The local SQLite setup stores the original image, predicted label, and corrected feedback label under `instance/feedback/`. Feedback is anonymous in this student version.

Feedback does not silently retrain or replace the production model. To include approved labels in the next model version:

```powershell
python training\retrain_from_feedback.py --database instance\visionai.db --dataset dataset --epochs 12
```

The command imports labeled feedback and writes the newly trained `model.keras` and `class_names.json` directly to `inference_service\`, which is the artifact directory used by the local and Docker inference service. Restart the inference service after retraining so it reloads the new model; the service caches the model in memory. Review the resulting evaluation metrics before deploying it. For production, use managed storage and authenticated user/session identifiers before enabling shared feedback collection.

The baseline dataset is intentionally small, so unseen breeds, dark images, multiple animals, or obstructed subjects can still be misclassified. Add a larger, licensed, diverse dataset and review the test metrics before treating predictions as production-grade.

## Local setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`. For local Flask development, assets are served from `public/`; Vercel serves the same directory through its CDN.

### Run the local inference service

The Flask web gateway and TensorFlow inference service run as separate processes. If `.env` contains `INFERENCE_API_URL=http://127.0.0.1:8001`, start the model service in a second PowerShell window before uploading images:

```powershell
python -c "from inference_service.app import app; app.run(host='127.0.0.1', port=8001, debug=False)"
```

Wait for the first model load to finish, then verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```

It should return `"ready": true`. The gateway health check at `http://127.0.0.1:5000/api/health` should then report `"inference": {"ready": true}`. In production, deploy `inference_service` using the included Dockerfile/Render blueprint and set `INFERENCE_API_URL` to that HTTPS service URL instead of `127.0.0.1`.

### Prediction API

The browser uses `POST /api/predict` with a multipart `image` field. `POST /predict` is also available as a compatibility alias for clients integrating directly with the gateway. Both routes validate file type and size, then return:

```json
{
  "success": true,
  "prediction": {
    "label": "cat",
    "confidence": 0.965,
    "probabilities": {"cat": 0.965, "dog": 0.035}
  },
  "prediction_id": 1
}
```

### Advanced profile and safety behavior

- **OOD guardrail:** results below `OOD_CONFIDENCE_THRESHOLD` (default `0.62`) are returned as `is_pet: false` with an explicit upload warning. Tune this using the environment variable after evaluating your model on non-pet images.
- **Breed and traits:** the gateway returns a stable `profile` schema (`breed`, `breed_confidence`, `traits`, and `care`). The current baseline is intentionally labeled a mixed-breed estimate; replace `enrich_prediction` in `app.py` with a validated breed/attribute model rather than presenting heuristic output as clinical or breed certainty.
- **Health Check:** the toggle returns a screening state and mandatory veterinary disclaimer. It does not diagnose disease. Connect a separately validated veterinary anomaly model before enabling automated alerts.
- **Active learning:** corrected feedback is stored in the configured feedback directory as a pending JSON manifest linked to the original uploaded image, and is also recorded in SQLite.

## Training

Prepare `dataset/train`, `dataset/validation`, and `dataset/test`, each containing `cats` and `dogs`. Use a licensed Cats vs Dogs dataset and keep the dataset out of Git.

```powershell
pip install tensorflow-cpu scikit-learn
New-Item -ItemType Directory artifacts -Force
python training\train.py --dataset dataset --epochs 12
```

Copy the resulting `models/model.keras` and `models/class_names.json` to the inference service host. Training is never performed during web requests.

## Inference service

```powershell
pip install -r inference_service\requirements.txt
$env:MODEL_PATH="C:\absolute\path\to\models\model.keras"
$env:CLASS_NAMES_PATH="C:\absolute\path\to\models\class_names.json"
$env:INFERENCE_API_KEY="change-this"
gunicorn --bind 0.0.0.0:8000 inference_service.app:app
```

Set `INFERENCE_API_URL` and the matching `INFERENCE_API_KEY` in the Flask environment. Use HTTPS for a hosted service.

### Public inference deployment

Vercel hosts the lightweight Flask gateway; it cannot host this TensorFlow service reliably. The included `inference_service\Dockerfile` and `render.yaml` deploy the model API to Render:

1. Push the repository to GitHub.
2. In Render, choose **New > Blueprint** and select this repository.
3. Set a strong `INFERENCE_API_KEY` when Render asks for the secret.
4. Copy the deployed service URL into Vercel as `INFERENCE_API_URL` and add the same API key as `INFERENCE_API_KEY`.
5. Redeploy Vercel and verify `/api/health` returns `"ready": true`.

The model artifact must be present at `inference_service\model.keras` and its labels at `inference_service\class_names.json` before creating the Render service.

## Tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

## Vercel deployment

1. Push this project to GitHub.
2. Import the repository into Vercel or install the current CLI.
3. Configure `INFERENCE_API_URL`, `INFERENCE_API_KEY`, and an external `DATABASE_URL` in Vercel.
4. Deploy with `vc deploy` (Vercel CLI 48.2.10 or newer).
5. Verify `/`, `/css/style.css`, `/api/health`, an invalid upload, and a real prediction.

Vercel's current Flask runtime discovers the root `app.py` and its `app` instance. Static files belong in `public/`. Vercel filesystem storage is not persistent, so use managed PostgreSQL for production history; `sqlite:///...` is for local development only.

## Limitations and next steps

The metrics page remains unavailable until real evaluation artifacts are generated and published. Anonymous history is intentionally not exposed across users; production deployments should add authenticated user identifiers before enabling shared persistence. Future work can add multi-class labels, authentication, feedback, and model version management.
