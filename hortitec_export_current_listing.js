/*
  Ejecuta este script en la consola del navegador estando en un listado de Hortitec
  como https://hortitec.es/catalogo/list o una categoría concreta.

  Exporta los productos cargados por scroll a un CSV compatible con:
  python manage.py import_products data/hortitec_catalog.csv --rewrite-descriptions
*/
(async () => {
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const seen = new Map();
  const maxIdleRounds = 8;
  let idleRounds = 0;
  let previousCount = 0;

  function text(selector, root = document) {
    return root.querySelector(selector)?.textContent?.trim().replace(/\s+/g, " ") || "";
  }

  function cleanPrice(value) {
    return value.replace(/[^\d,.]/g, "").replace(",", ".");
  }

  function activeCategory() {
    const active = document.querySelector(".fblock--categories .active .f-name");
    const title = active?.textContent?.trim();
    return title || "Catálogo Hortitec";
  }

  function collectProducts() {
    document.querySelectorAll(".product.list").forEach((card) => {
      const sku = text(".pl-ref span", card);
      const name = text(".pl-name h3", card);
      if (!sku || !name || /^Ref\.$/i.test(sku)) return;

      const sourcePath = card.querySelector(".pl-name a[href], .pl-img a[href]")?.getAttribute("href") || "";
      const imageUrl = card.querySelector(".pl-img img")?.src || "";
      const product = {
        sku,
        name,
        category: activeCategory(),
        supplier: text(".pl-brand", card) || "Hortitec",
        price: cleanPrice(text(".pl-pvp span", card)),
        compare_at_price: "",
        image_url: imageUrl,
        source_url: sourcePath ? new URL(sourcePath, location.origin).href : location.href,
        featured: "",
        is_new: "",
        description: "",
      };
      seen.set(product.sku, product);
    });
  }

  while (idleRounds < maxIdleRounds) {
    collectProducts();
    window.scrollTo(0, document.documentElement.scrollHeight);
    await wait(1200);
    collectProducts();

    if (seen.size === previousCount) {
      idleRounds += 1;
    } else {
      idleRounds = 0;
      previousCount = seen.size;
      console.log(`Productos detectados: ${seen.size}`);
    }
  }

  const headers = [
    "sku",
    "name",
    "category",
    "supplier",
    "price",
    "compare_at_price",
    "image_url",
    "source_url",
    "featured",
    "is_new",
    "description",
  ];

  const escapeCell = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const csv = [
    headers.join(","),
    ...[...seen.values()].map((product) => headers.map((header) => escapeCell(product[header])).join(",")),
  ].join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `hortitec-${activeCategory().toLowerCase().replaceAll(" ", "-")}-${seen.size}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  console.log(`CSV exportado con ${seen.size} productos.`);
})();

