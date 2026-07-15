document.addEventListener("DOMContentLoaded", () => {

    const toggles = document.querySelectorAll(".category-toggle");

    toggles.forEach(toggle => {

        toggle.addEventListener("click", () => {

            const currentList = toggle.nextElementSibling;
            const currentIcon = toggle.querySelector(".toggle-icon");

            document.querySelectorAll(".subcategory-list").forEach(list => {

                if (list !== currentList) {
                    list.classList.remove("open");
                }

            });

            document.querySelectorAll(".toggle-icon").forEach(icon => {

                if (icon !== currentIcon) {
                    icon.textContent = "▶";
                }

            });

            currentList.classList.toggle("open");

            currentIcon.textContent =
                currentList.classList.contains("open")
                    ? "▼"
                    : "▶";

        });

    });

});