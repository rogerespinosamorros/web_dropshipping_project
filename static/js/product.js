document.addEventListener("DOMContentLoaded", () => {

    const radios = document.querySelectorAll(".variant-card input");

    const price = document.getElementById("product-price");
    const sku = document.getElementById("product-sku");
    const stock = document.getElementById("product-stock");

    if (!radios.length) return;

    function update(card){

        price.textContent = `${card.dataset.price} €`;

        sku.textContent = card.dataset.sku;

        stock.textContent = card.dataset.stock;

    }

    radios.forEach((radio) => {

        if (radio.checked){
            update(radio.closest(".variant-card"));
        }

        radio.addEventListener("change", () => {
            update(radio.closest(".variant-card"));
        });

    });

});