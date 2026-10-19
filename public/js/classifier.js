const form = document.querySelector("#classifier-form");
if (form) {
  const input = document.querySelector("#image-input"), preview = document.querySelector("#preview");
  const image = document.querySelector("#preview-image"), message = document.querySelector("#form-message");
  input.addEventListener("change", () => {
    const file = input.files[0]; if (!file) return;
    image.src = URL.createObjectURL(file); document.querySelector("#file-name").textContent = file.name;
    document.querySelector("#file-meta").textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
    preview.classList.remove("hidden"); message.textContent = "";
  });
  document.querySelector("#remove-image").addEventListener("click", () => { input.value = ""; preview.classList.add("hidden"); });
  form.addEventListener("submit", async (event) => {
    event.preventDefault(); message.textContent = "Analyzing…";
    const button = document.querySelector("#classify-button"); button.disabled = true;
    try {
      const response = await fetch("/api/predict", {method:"POST", body:new FormData(form)});
      const data = await response.json(); if (!response.ok || !data.success) throw new Error(data.error || "Prediction failed.");
      const prediction = data.prediction, confidence = Number(prediction.confidence);
      form.dataset.predictionId = data.prediction_id || "";
      document.querySelector("#result").classList.remove("hidden"); document.querySelector("#result-label").textContent = prediction.label;
      document.querySelector("#result-confidence").textContent = `${(confidence * 100).toFixed(1)}%`;
      document.querySelector("#confidence-bar").style.width = `${confidence * 100}%`;
      document.querySelector("#result-meta").textContent = `${prediction.model_version || "unknown model"} · ${prediction.inference_ms ?? "—"} ms`;
      document.querySelector("#probabilities").replaceChildren(...Object.entries(prediction.probabilities || {}).map(([label, value]) => { const row=document.createElement("div"); row.className="probability"; row.textContent=`${label}: ${(Number(value)*100).toFixed(1)}%`; return row; }));
      document.querySelector("#feedback").classList.remove("hidden");
      message.textContent = "";
    } catch (error) { message.textContent = error.message; } finally { button.disabled = false; }
  });
  document.querySelectorAll(".feedback-button").forEach((button) => button.addEventListener("click", async () => {
    const feedbackMessage = document.querySelector("#feedback-message");
    try {
      const response = await fetch("/api/feedback", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({prediction_id: form.dataset.predictionId, label: button.dataset.label})});
      const data = await response.json(); if (!response.ok || !data.success) throw new Error(data.error || "Feedback could not be saved.");
      feedbackMessage.textContent = " Saved — thank you!";
    } catch (error) { feedbackMessage.textContent = ` ${error.message}`; }
  }));
}
