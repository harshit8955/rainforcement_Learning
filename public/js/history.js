async function loadHistory() {
  const response = await fetch("/api/history"); const data = await response.json();
  document.querySelector("#history-status").textContent = data.persistent ? "Stored locally for development." : "Persistence is not configured; history is unavailable.";
  document.querySelector("#history-body").replaceChildren(...data.items.map(item => { const row=document.createElement("tr"); [item.filename,item.label,`${(item.confidence*100).toFixed(1)}%`,new Date(item.created_at).toLocaleString()].forEach(value=>{const cell=document.createElement("td");cell.textContent=value;row.append(cell);});return row;}));
}
loadHistory();
document.querySelector("#clear-history")?.addEventListener("click", async()=>{if(confirm("Clear prediction history?")){await fetch("/api/history",{method:"DELETE"});loadHistory();}});

