const form = document.querySelector("#classifier-form");

if (form) {
  const input = document.querySelector("#image-input");
  const dropzone = document.querySelector("#dropzone");
  const preview = document.querySelector("#preview");
  const previewImage = document.querySelector("#preview-image");
  const message = document.querySelector("#form-message");
  const submit = document.querySelector("#classify-button");
  let objectUrl = "";
  let feedbackLabel = "";

  const setMessage = (text, error = true) => {
    message.textContent = text;
    message.classList.toggle("is-success", !error);
  };

  const selectFile = (file) => {
    if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type)) return setMessage("Please choose a JPG or PNG image.");
    if (file.size > 10 * 1024 * 1024) return setMessage("That image is larger than the 10 MB limit.");
    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    previewImage.src = objectUrl;
    document.querySelector("#file-name").textContent = file.name;
    document.querySelector("#file-meta").textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
    preview.classList.remove("hidden");
    setMessage("", false);
  };

  input.addEventListener("change", () => selectFile(input.files[0]));
  ["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.add("is-dragging");
  }));
  ["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.remove("is-dragging");
  }));
  dropzone.addEventListener("drop", (event) => selectFile(event.dataTransfer.files[0]));
  document.querySelector("#remove-image").addEventListener("click", () => {
    input.value = "";
    preview.classList.add("hidden");
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = "";
    setMessage("", false);
  });

  const renderPrediction = (prediction) => {
    const confidence = Number(prediction.confidence);
    const isPet = prediction.is_pet !== false;
    document.querySelector("#result-label").textContent = isPet ? prediction.label : "Not a pet";
    document.querySelector("#result-confidence").textContent = `${(confidence * 100).toFixed(1)}%`;
    document.querySelector("#confidence-value").textContent = `${(confidence * 100).toFixed(1)}%`;
    document.querySelector("#confidence-bar").style.width = `${confidence * 100}%`;
    const warning = document.querySelector("#ood-warning");
    const profileContent = document.querySelector("#profile-content");
    if (warning) warning.classList.toggle("hidden", isPet);
    if (profileContent) profileContent.classList.toggle("hidden", !isPet);
    document.querySelector("#result-meta").textContent = `${prediction.model_version || "PetVision model"} · ${prediction.inference_ms ?? prediction.gateway_ms ?? "—"} ms`;
    document.querySelector("#probabilities").replaceChildren(...Object.entries(prediction.probabilities || {}).map(([label, value]) => {
      const row = document.createElement("div");
      row.className = "probability";
      row.innerHTML = `<div class="probability-label"><span class="class-dot ${label.toLowerCase()}"></span><strong>${label}</strong><b>${(Number(value) * 100).toFixed(1)}%</b></div><div class="probability-bar"><i style="width:${Number(value) * 100}%"></i></div>`;
      return row;
    }));
    if (!isPet || !prediction.profile) return;
    const profile = prediction.profile;
    document.querySelector("#breed-name").textContent = profile.breed;
    document.querySelector("#breed-confidence").textContent = `${(Number(profile.breed_confidence) * 100).toFixed(0)}% confidence`;
    document.querySelector("#trait-pills").replaceChildren(...Object.entries(profile.traits || {}).map(([name, value]) => {
      const pill = document.createElement("span");
      pill.textContent = `${name.replace("_", " ")}: ${value}`;
      return pill;
    }));
    document.querySelector("#care-cards").replaceChildren(...Object.entries(profile.care || {}).map(([name, value]) => {
      const card = document.createElement("div");
      card.innerHTML = `<strong>${name}</strong><p>${value}</p>`;
      return card;
    }));
    const health = prediction.health_check || {};
    const healthPanel = document.querySelector("#health-panel");
    if (healthPanel) healthPanel.classList.toggle("hidden", !health.enabled);
    if (health.enabled) {
      document.querySelector("#health-alert").textContent = (health.alerts || []).join(" ");
      document.querySelector("#health-disclaimer").textContent = health.disclaimer;
    }
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!input.files[0]) return setMessage("Choose an image before analyzing.");
    submit.disabled = true;
    submit.innerHTML = '<span class="spinner"></span> Analyzing image…';
    setMessage("", false);
    try {
      const response = await fetch("/api/predict", { method: "POST", body: new FormData(form) });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || "Prediction failed.");
      form.dataset.predictionId = data.prediction_id || "";
      document.querySelector("#result-preview").src = previewImage.src;
      renderPrediction(data.prediction);
        const result = document.querySelector("#result");
        const feedback = document.querySelector("#feedback");
        const correction = document.querySelector("#correction");
        if (result) {
          result.classList.remove("hidden");
          result.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        if (feedback) feedback.classList.remove("hidden");
        if (correction) correction.classList.add("hidden");
    } catch (error) {
      setMessage(error.message);
    } finally {
      submit.disabled = false;
      submit.innerHTML = '<span class="button-icon">✦</span> Analyze image';
    }
  });

  document.querySelectorAll(".feedback-button").forEach((button) => button.addEventListener("click", async () => {
    const messageTarget = document.querySelector("#feedback-message");
    document.querySelectorAll(".feedback-button").forEach((item) => { item.disabled = true; });
    const predictedLabel = document.querySelector("#result-label").textContent.toLowerCase();
    feedbackLabel = predictedLabel === "cat" || predictedLabel === "dog" ? predictedLabel : button.dataset.label;
    const isCorrect = button.dataset.feedback === "correct";
    if (!isCorrect) {
      const correction = document.querySelector("#correction");
      if (correction) correction.classList.remove("hidden");
    }
    try {
      const response = await fetch("/api/feedback", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prediction_id: form.dataset.predictionId,
          label: feedbackLabel,
          feedback: isCorrect ? "correct" : "incorrect"
        })
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || "Feedback could not be saved.");
      messageTarget.textContent = "Thanks — feedback saved.";
    } catch (error) {
      messageTarget.textContent = error.message;
      document.querySelectorAll(".feedback-button").forEach((item) => { item.disabled = false; });
    }
  }));

  document.querySelector("#save-correction").addEventListener("click", async () => {
    const correctedBreed = document.querySelector("#corrected-breed").value;
    if (!correctedBreed) return;
    const correctedLabel = document.querySelector("#corrected-breed").selectedOptions[0].value;
    const response = await fetch("/api/feedback", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prediction_id: form.dataset.predictionId, label: correctedLabel, corrected_breed: document.querySelector("#corrected-breed").selectedOptions[0].textContent })
    });
    const data = await response.json();
    document.querySelector("#feedback-message").textContent = data.success ? "Correction queued for active learning." : (data.error || "Correction could not be saved.");
  });
}
