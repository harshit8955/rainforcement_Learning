const themeButton = document.querySelector(".theme-toggle");
const savedTheme = localStorage.getItem("visionai-theme") || "light";

function applyTheme(theme) {
  const isDark = theme === "dark";
  document.documentElement.dataset.theme = isDark ? "dark" : "light";
  if (themeButton) {
    themeButton.setAttribute("aria-pressed", String(isDark));
    themeButton.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
  }
}

applyTheme(savedTheme);
themeButton?.addEventListener("click", () => {
  const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("visionai-theme", nextTheme);
  applyTheme(nextTheme);
});
