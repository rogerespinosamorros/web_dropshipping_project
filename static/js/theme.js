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


function attachBrandFilter() {

    const input = document.getElementById("brand-filter");

    if (!input) return;

    const items = document.querySelectorAll(".brand-link");

    input.addEventListener("input", () => {

        const value = input.value.toLowerCase().trim();

        items.forEach(item => {

            item.style.display = item.textContent
                .toLowerCase()
                .includes(value)
                ? ""
                : "none";

        });

    });

}


function attachCategoryFilter() {

    const input = document.getElementById("category-filter");

    if (!input) return;

    const groups = document.querySelectorAll(".filter-group");

    input.addEventListener("input", () => {

        const value = input.value.toLowerCase().trim();

        groups.forEach(group => {

            const links = group.querySelectorAll(".category-link");

            let visible = false;

            links.forEach(link => {

                const match = link.textContent
                    .toLowerCase()
                    .includes(value);

                link.style.display = match ? "" : "none";

                if (match) {
                    visible = true;
                }

            });

            group.style.display = visible ? "" : "none";

        });

    });

}

document.addEventListener("DOMContentLoaded", () => {

    attachBrandFilter();
    attachCategoryFilter();

});