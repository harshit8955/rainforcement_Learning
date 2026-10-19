import time

import requests


class InferenceClientError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


class InferenceClient:
    def __init__(self, base_url, api_key, timeout):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def health(self):
        if not self.base_url:
            return {
                "configured": False,
                "ready": False,
                "error": "Set INFERENCE_API_URL to a running inference service.",
            }
        try:
            response = requests.get(f"{self.base_url}/health", headers=self._headers(), timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return {
                "configured": True,
                "ready": bool(data.get("ready", True)),
                **({"error": data["error"]} if data.get("error") else {}),
            }
        except (requests.RequestException, ValueError):
            return {
                "configured": True,
                "ready": False,
                "error": "The inference service is unreachable or returned invalid JSON.",
            }

    def predict(self, image):
        if not self.base_url:
            raise InferenceClientError("Inference is not configured. Set INFERENCE_API_URL.", 503)
        started = time.perf_counter()
        try:
            response = requests.post(
                f"{self.base_url}/predict",
                files={"image": (image.filename, image.stream, image.mimetype)},
                headers=self._headers(),
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                raise InferenceClientError("The inference service rejected the image.", 502)
            data = response.json()
            if not data.get("success") or not data.get("prediction"):
                raise InferenceClientError("The inference service returned an invalid response.", 502)
            result = data["prediction"]
            result.setdefault("gateway_ms", round((time.perf_counter() - started) * 1000))
            return result
        except requests.Timeout as exc:
            raise InferenceClientError("The inference service timed out.", 504) from exc
        except requests.RequestException as exc:
            raise InferenceClientError("The inference service is unavailable.", 502) from exc
        except ValueError as exc:
            raise InferenceClientError("The inference service returned invalid JSON.", 502) from exc
