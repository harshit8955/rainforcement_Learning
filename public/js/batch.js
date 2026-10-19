const batchInput = document.querySelector("#batch-input");
document.querySelector("#batch-submit")?.addEventListener("click", async () => {
  const message = document.querySelector("#batch-message"); if (!batchInput.files.length) { message.textContent = "Select images first."; return; }
  const form = new FormData(); [...batchInput.files].forEach(file => form.append("images", file)); message.textContent = "Analyzing…";
  try { const response=await fetch("/api/predict/batch",{method:"POST",body:form}); const data=await response.json(); if(!response.ok||!data.success) throw new Error(data.error); const container=document.querySelector("#batch-results"); container.replaceChildren(...data.results.map(result=>{const row=document.createElement("p");row.textContent=`${result.filename}: ${result.success ? `${result.label} (${(result.confidence*100).toFixed(1)}%)` : result.error}`;return row;})); message.textContent=""; } catch(error){message.textContent=error.message;}
});
document.querySelector("#batch-clear")?.addEventListener("click",()=>{batchInput.value="";document.querySelector("#batch-results").replaceChildren();});

