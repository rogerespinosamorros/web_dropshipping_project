# Cultiva

MVP de ecommerce y dropshipping desarrollado con Django. Está inspirado en las funciones de un distribuidor con catálogo amplio, pero plantea una experiencia más limpia, moderna y enfocada a conversión.

## Incluye

- Portada responsive con categorías y productos destacados.
- Catálogo con búsqueda y filtro por categoría.
- Fichas de producto y productos relacionados.
- Carrito basado en sesión.
- Panel de administración para productos, categorías y proveedores.
- Comando para cargar un catálogo demo.

## Puesta en marcha

Necesitas Python 3.11 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py seed_catalog
python manage.py import_products data/catalog_sample.csv --rewrite-descriptions
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. El panel de administración estará en `http://127.0.0.1:8000/admin/`.

## Próximas fases recomendadas

1. Definir proveedor y formato de sincronización de catálogo, stock y pedidos.
2. Integrar Stripe o Redsys y crear el flujo de checkout.
3. Añadir cuentas de cliente, direcciones, emails y seguimiento de pedidos.
4. Configurar PostgreSQL, almacenamiento de imágenes y despliegue.

## Importar productos

El proyecto incluye un importador masivo:

```powershell
python manage.py import_products data/catalog_sample.csv --rewrite-descriptions
```

Columnas soportadas: `sku`, `name`, `category`, `supplier`, `price`, `compare_at_price`, `image_url`, `source_url`, `featured`, `is_new`, `description`.

Para datos de terceros conviene importar datos factuales como nombre, SKU, precio, categoría e imagen, y generar descripciones propias con `--rewrite-descriptions` en vez de copiar textos completos de otra tienda.

Para Hortitec, consulta `IMPORTAR_HORTITEC.md`. Incluye un script de navegador para exportar listados grandes a CSV.
