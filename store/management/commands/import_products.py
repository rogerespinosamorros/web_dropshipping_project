"""
Importador de catálogo Hortitec desde CSV.

Uso:
    python manage.py import_products data/hortitec_catalogo.csv
    python manage.py import_products data/hortitec_catalogo.csv --dry-run
    python manage.py import_products data/hortitec_catalogo.csv --clear

Lógica de agrupación de variantes:
    - variante=false → Product simple sin ProductVariant
    - variante=true  → se agrupa por nombre exacto; cada grupo genera un Product
                       con has_variants=True y una ProductVariant por fila
    - Si un nombre aparece en ambos (false y true), se tratan todos como variantes.
"""

import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from itertools import product
from pathlib import Path

from PIL.TiffTags import lookup
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.views import defaults
from django.views import defaults

from store.models import Brand, Category, Product, ProductVariant, Supplier


class Command(BaseCommand):
    help = "Importa el catálogo Hortitec desde CSV (con soporte de variantes y categorías anidadas)."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Ruta al archivo .csv")
        parser.add_argument(
            "--supplier",
            default="Hortitec",
            help="Nombre del proveedor (default: Hortitec)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Analiza el archivo sin guardar nada.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Elimina todos los productos antes de importar (re-importación limpia).",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"No existe el archivo: {path}")

        rows = self._load_csv(path)
        self.stdout.write(f"Filas leídas: {len(rows)}")

        groups = self._group_rows(rows)
        self.stdout.write(
            f"Grupos: {len(groups['simple'])} simples, "
            f"{len(groups['with_variants'])} con variantes"
        )

        if options["dry_run"]:
            self._dry_run_report(groups)
            return

        if options["clear"]:
            self.stdout.write(self.style.WARNING("Eliminando productos existentes…"))
            ProductVariant.objects.all().delete()
            Product.objects.all().delete()
            self.stdout.write(self.style.WARNING("Productos eliminados."))

        with transaction.atomic():
            supplier = Supplier.objects.get_or_create(name=options["supplier"])[0]
            stats = self._import(groups, supplier)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nImportación completada:\n"
                f"  Categorías: {stats['categories']} (padre) + {stats['subcategories']} (hijo)\n"
                f"  Marcas:     {stats['brands']}\n"
                f"  Productos:  {stats['products_created']} creados, "
                f"{stats['products_updated']} actualizados\n"
                f"  Variantes:  {stats['variants_created']} creadas, "
                f"{stats['variants_updated']} actualizadas\n"
            )
        )
    def _value(self, row, *keys, default=""):
        """
        Devuelve el primer valor existente entre varias posibles columnas.

        Ejemplo:
            self._value(row, "nombre", "name")
        """
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                return value
        return default
    # ------------------------------------------------------------------
    # Carga y agrupación
    # ------------------------------------------------------------------

    def _load_csv(self, path):
        with path.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def _group_rows(self, rows):
        """
        Devuelve:
          groups['simple']        → lista de filas únicas sin variante
          groups['with_variants'] → dict {nombre: [filas]} para productos con variantes
        """
        variante_true  = defaultdict(list)
        variante_false = {}

        for row in rows:

            nombre = self._value(row, "nombre", "name").strip()

            variante = (
                self._value(row, "variante", "has_variants", default="false")
                .strip()
                .lower()
            )

            if variante == "true":
                variante_true[nombre].append(row)
            else:
                variante_false[nombre] = row

        # Nombres que aparecen en ambos → se tratan como variantes
        solapados = set(variante_false.keys()) & set(variante_true.keys())
        for nombre in solapados:
            variante_true[nombre].append(variante_false.pop(nombre))

        simple = list(variante_false.values())
        with_variants = dict(variante_true)

        return {"simple": simple, "with_variants": with_variants}

    # ------------------------------------------------------------------
    # Importación real
    # ------------------------------------------------------------------

    def _import(self, groups, supplier):
        stats = {
            "categories": 0,
            "subcategories": 0,
            "brands": 0,
            "products_created": 0,
            "products_updated": 0,
            "variants_created": 0,
            "variants_updated": 0,
        }
        category_cache = {}
        brand_cache = {}

        # Productos simples
        for row in groups["simple"]:
            category = self._get_or_create_category(row["categoria"], category_cache, stats)
            brand = self._get_or_create_brand(row.get("fabricante", ""), brand_cache, stats)
            created = self._upsert_simple_product(row, category, brand, supplier)
            if created:
                stats["products_created"] += 1
            else:
                stats["products_updated"] += 1

        # Productos con variantes
        for nombre, rows in groups["with_variants"].items():
            # Usar la categoría y marca de la primera fila del grupo
            first = rows[0]
            category = self._get_or_create_category(first["categoria"], category_cache, stats)
            brand = self._get_or_create_brand(first.get("fabricante", ""), brand_cache, stats)
            product, p_created = self._upsert_product_with_variants(nombre, first, category, brand, supplier)
            if p_created:
                stats["products_created"] += 1
            else:
                stats["products_updated"] += 1

            for row in rows:
                v_created = self._upsert_variant(product, row)
                if v_created:
                    stats["variants_created"] += 1
                else:
                    stats["variants_updated"] += 1

        return stats

    def _get_or_create_category(self, categoria_raw, cache, stats):
        """
        Formato CSV: "Padre > Hijo"  →  Category(name=Hijo, parent=Category(name=Padre))
        También acepta "Solo" sin separador.
        """
        key = categoria_raw.strip()
        if key in cache:
            return cache[key]

        parts = [p.strip() for p in key.split(">")]
        if len(parts) == 2:
            padre_name, hijo_name = parts[0], parts[1]
            padre = cache.get(f"__root__{padre_name}")
            if padre is None:
                padre, created = Category.objects.get_or_create(
                    name=padre_name, parent=None
                )
                if created:
                    stats["categories"] += 1
                cache[f"__root__{padre_name}"] = padre

            hijo, created = Category.objects.get_or_create(
                name=hijo_name, parent=padre
            )
            if created:
                stats["subcategories"] += 1
            cache[key] = hijo
            return hijo
        else:
            cat, created = Category.objects.get_or_create(name=key, parent=None)
            if created:
                stats["categories"] += 1
            cache[key] = cat
            return cat

    def _get_or_create_brand(self, fabricante_raw, cache, stats):
        name = fabricante_raw.strip()
        if not name:
            return None
        if name in cache:
            return cache[name]
        brand, created = Brand.objects.get_or_create(name=name)
        if created:
            stats["brands"] += 1
        cache[name] = brand
        return brand

    def _upsert_simple_product(self, row, category, brand, supplier):
        """Crea o actualiza un Product sin variantes. Devuelve True si fue creado."""
        price = self._money(row.get("precio", "0"))
        pvp = self._optional_money(row.get("pvp"))
        defaults = {
            "name": row["nombre"].strip(),
            "category": category,
            "brand": brand,
            "supplier": supplier,
            "price": price,
            "pvp": pvp,
            "image_url": (row.get("imagen") or "").strip()[:500],
            "source_url": (row.get("url") or "").strip()[:500],
            "hortitec_id": hortitec_id,
            "has_variants": False,
            "featured": self._flag(row.get("featured")),
            "outlet": self._flag(row.get("outlet")),
            "active": self._flag(row.get("disponible")),
        }
        # Usamos el hortitec_id como identificador único
        slug = self._unique_slug_for(row["nombre"].strip())
        hortitec_id = (row.get("id") or "").strip()

        lookup = {}

        if hortitec_id:
            lookup["hortitec_id"] = hortitec_id
        else:
            lookup["slug"] = slug

        _, created = Product.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )
        # El producto se sincroniza utilizando el identificador estable de Hortitec.
        return created

    def _upsert_product_with_variants(self, nombre, first_row, category, brand, supplier):
        """Crea o actualiza el Product padre de un grupo de variantes."""
        price = self._money(first_row.get("precio", "0"))
        pvp = self._optional_money(first_row.get("pvp"))
        slug = self._unique_slug_for(nombre)

        hortitec_id = (first_row.get("id") or "").strip()

        lookup = {}

        if hortitec_id:
            lookup["hortitec_id"] = hortitec_id
        else:
            lookup["slug"] = slug

        product, created = Product.objects.update_or_create(
            **lookup,
            defaults={
                "name": nombre,
                "category": category,
                "brand": brand,
                "supplier": supplier,
                "price": price,
                "pvp": pvp,
                "image_url": (first_row.get("imagen") or "").strip()[:500],
                "source_url": (first_row.get("url") or "").strip()[:500],
                "hortitec_id": hortitec_id,
                "has_variants": True,
                "featured": self._flag(first_row.get("featured")),
                "outlet": self._flag(first_row.get("outlet")),
                "active": self._flag(first_row.get("disponible")),
            },
        )

        return product, created

    def _upsert_variant(self, product, row):
        """Crea o actualiza una ProductVariant. Devuelve True si fue creada."""
        sku = row["sku"].strip()
        price = self._money(row.get("precio", "0"))
        pvp = self._optional_money(row.get("pvp"))
        attributes = self._parse_attributes(row.get("atributos", ""))

        _, created = ProductVariant.objects.update_or_create(
            sku=sku,
            defaults={
                "product": product,
                "hortitec_id": (row.get("id") or "").strip(),
                "attributes": attributes,
                "price": price,
                "pvp": pvp,
                "image_url": (row.get("imagen") or "").strip()[:500],
                "stock": self._flag(row.get("stock")),
                "stock_level": (row.get("stock_level") or "").strip(),
                "active": self._flag(row.get("disponible")),
            },
        )
        return created

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _parse_attributes(self, raw):
        """
        Parsea "clave: valor | clave: valor" → {"clave": "valor", ...}
        Ignora segmentos sin ':'.
        """
        attrs = {}
        if not raw:
            return attrs
        for segment in raw.split("|"):
            segment = segment.strip()
            if ":" not in segment:
                continue
            key, _, value = segment.partition(":")
            key = key.strip()
            value = value.strip()
            if key and value:
                attrs[key] = value
        return attrs

    def _unique_slug_for(self, name):
        """
        Devuelve el slug existente si el nombre ya está en BD,
        o genera uno nuevo único. No crea nada en BD.
        """
        from django.utils.text import slugify
        base = slugify(name)
        # Si ya existe un producto con ese slug, lo reutilizamos (update_or_create lo encontrará)
        return base

    def _money(self, value):
        v = str(value or "0").strip().replace(",", ".")
        try:
            return Decimal(v)
        except InvalidOperation:
            return Decimal("0")

    def _optional_money(self, value):
        if not value or not str(value).strip():
            return None
        return self._money(value)

    def _flag(self, value):
        return str(value or "").strip().lower() in {"1", "true", "yes", "si", "sí", "x"}

    # ------------------------------------------------------------------
    # Dry-run
    # ------------------------------------------------------------------

    def _dry_run_report(self, groups):
        total_variants = sum(len(v) for v in groups["with_variants"].values())
        self.stdout.write("\n--- DRY RUN (sin cambios en BD) ---")
        self.stdout.write(f"Productos simples que se crearían:       {len(groups['simple'])}")
        self.stdout.write(f"Productos con variantes que se crearían: {len(groups['with_variants'])}")
        self.stdout.write(f"Variantes totales que se crearían:       {total_variants}")
        self.stdout.write(f"Total filas procesadas:                  {len(groups['simple']) + total_variants}")

        # Muestra algunos ejemplos de productos con variantes
        self.stdout.write("\nEjemplos de agrupación (primeros 5):")
        for nombre, rows in list(groups["with_variants"].items())[:5]:
            self.stdout.write(f"  · {nombre} ({len(rows)} variantes)")
            for r in rows[:3]:
                attrs = self._parse_attributes(r.get("atributos", ""))
                self.stdout.write(f"      SKU {r['sku']} | {attrs}")
