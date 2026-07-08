document.addEventListener("DOMContentLoaded", () => {

    const radios = document.querySelectorAll(".variant-card input");

    if (!radios.length) return;

    const price = document.getElementById("product-price");
    const sku = document.getElementById("product-sku");
    const stock = document.getElementById("product-stock");
    const image = document.getElementById("product-image");
    const specs = document.getElementById("product-specs");

    function formatKey(key){

    return key
        .replaceAll("-", " ")
        .replace(/\b\w/g, c => c.toUpperCase());

    }

    function update(card){

        // Precio
        price.textContent = `${card.dataset.price} €`;

        // Referencia
        sku.textContent = card.dataset.sku;

        // Stock
        stock.textContent = card.dataset.stock;

        stock.className = card.dataset.stock === "En stock"
            ? "stock-ok"
            : "stock-ko";

        // Imagen
        if(image && card.dataset.image){
            image.src = card.dataset.image;
        }

        // Especificaciones
        if(specs && card.dataset.attributes){
            const attributes = JSON.parse(card.dataset.attributes);

            let html = `
                <table class="spec-table">
                    <tbody>
            `;

            Object.entries(attributes).forEach(([key,value])=>{

                html += `
                    <tr>
                        <th>${formatKey(key)}</th>
                        <td>${value}</td>
                    </tr>
                `;

            });

            html += `
                    </tbody>
                </table>
            `;

            specs.innerHTML = html;

        }

    }

    radios.forEach((radio)=>{

        if(radio.checked){
            update(radio.closest(".variant-card"));
        }

        radio.addEventListener("change",()=>{

            update(radio.closest(".variant-card"));

        });

    });

});