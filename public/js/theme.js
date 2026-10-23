const savedTheme = localStorage.getItem("visionai-theme") || "light";
document.documentElement.dataset.theme = savedTheme;
document.addEventListener("click", (event) => {
  if (!event.target.closest(".theme-toggle")) return;
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("visionai-theme", theme);
});
