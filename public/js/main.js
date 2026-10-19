const sidebar = document.querySelector(".sidebar");
document.querySelector(".menu-toggle")?.addEventListener("click", () => sidebar?.classList.toggle("open"));
document.querySelector(".sidebar-collapse")?.addEventListener("click", () => sidebar?.classList.toggle("open"));
