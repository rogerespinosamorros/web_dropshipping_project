# Importar catálogo de Hortitec

Hortitec muestra el catálogo como una app Nuxt con carga progresiva por scroll. La forma más sencilla de traer productos a este proyecto es exportar los datos factuales desde el navegador y luego importarlos con Django.

## Qué datos importamos

- SKU/referencia
- Nombre
- Categoría del listado
- Marca/proveedor
- Precio público
- Imagen pública
- URL de origen

No copiamos descripciones completas de Hortitec. El comando de importación puede generar descripciones propias con `--rewrite-descriptions`.

## Exportar CSV desde Hortitec

1. Abre `https://hortitec.es/catalogo/list`.
2. Abre las herramientas de desarrollador del navegador.
3. Pega el contenido de `hortitec_export_current_listing.js` en la consola.
4. Espera a que el script haga scroll y descargue el CSV.
5. Guarda el CSV dentro de `data/`, por ejemplo `data/hortitec_catalog.csv`.

Para conservar mejor las categorías, puedes repetir el proceso dentro de cada categoría de Hortitec, como `/riego/list` o `/fertilizantes/list`, y luego importar cada CSV.

## Importar en Django

```powershell
.\.venv\Scripts\python.exe manage.py import_products data\hortitec_catalog.csv --rewrite-descriptions
```

El importador es idempotente por `sku`: si vuelves a importar el mismo CSV, actualiza los productos existentes en vez de duplicarlos.

