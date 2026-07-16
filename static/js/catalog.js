document.addEventListener("DOMContentLoaded", () => {

    // Desplegar categorías

    document.querySelectorAll(".category-toggle").forEach(toggle => {

        toggle.addEventListener("click", (e) => {

            e.preventDefault();

            const group = toggle.closest(".category-group");

            const list = group.querySelector(".subcategory-list");

            if (!list) return;

            list.classList.toggle("open");

            toggle.classList.toggle("open");

            toggle.textContent = list.classList.contains("open") ? "▾" : "▸";

        });

    });


    // Buscador de categorías

    const categorySearch = document.getElementById("category-filter");

    if (categorySearch) {

        categorySearch.addEventListener("input", function () {

            const value = this.value.toLowerCase();

            document.querySelectorAll(".category-group").forEach(group => {

                const title = group.querySelector(".category-parent")
                    .textContent
                    .toLowerCase();

                group.style.display = title.includes(value)
                    ? ""
                    : "none";

            });

        });

    }


    // Buscador de marcas

    const brandSearch = document.getElementById("brand-filter");

    if (brandSearch) {

        brandSearch.addEventListener("input", function () {

            const value = this.value.toLowerCase();

            document.querySelectorAll(".brand-link").forEach(link => {

                link.style.display =
                    link.textContent.toLowerCase().includes(value)
                        ? ""
                        : "none";

            });

        });

    }

});