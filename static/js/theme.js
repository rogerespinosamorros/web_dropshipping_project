const themeToggle = document.querySelector("[data-theme-toggle]");
const root = document.documentElement;

function setThemeLabel() {
  if (!themeToggle) return;
  themeToggle.textContent = root.dataset.theme === "dark" ? "Modo claro" : "Modo oscuro";
}

if (!localStorage.getItem("theme") && window.matchMedia("(prefers-color-scheme: dark)").matches) {
  root.dataset.theme = "dark";
}

setThemeLabel();

themeToggle?.addEventListener("click", () => {
  const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = nextTheme;
  localStorage.setItem("theme", nextTheme);
  setThemeLabel();
});
