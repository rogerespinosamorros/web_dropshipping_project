import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from store.models import Category, Product, Supplier


class Command(BaseCommand):
    help = "Importa productos desde CSV o JSON y genera descripciones propias cuando falten."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Ruta al archivo .csv o .json")
        parser.add_argument("--supplier", default="Proveedor externo", help="Proveedor por defecto")
        parser.add_argument(
            "--rewrite-descriptions",
            action="store_true",
            help="Ignora descripciones entrantes y genera descripciones propias.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Valida el archivo sin guardar cambios.")

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"No existe el archivo: {path}")

        rows = self.load_rows(path)
        created = 0
        updated = 0
        supplier_cache = {}
        category_cache = {}

        for index, row in enumerate(rows, start=1):
            data = self.normalize_row(row, index, options)
            if options["dry_run"]:
                continue

            supplier = supplier_cache.get(data["supplier_name"])
            if supplier is None:
                supplier, _ = Supplier.objects.get_or_create(name=data["supplier_name"])
                supplier_cache[data["supplier_name"]] = supplier

            category = category_cache.get(data["category_name"])
            if category is None:
                category, _ = Category.objects.get_or_create(name=data["category_name"])
                category_cache[data["category_name"]] = category

            _, was_created = Product.objects.update_or_create(
                sku=data["sku"],
                defaults={
                    "name": data["name"],
                    "category": category,
                    "supplier": supplier,
                    "description": data["description"],
                    "price": data["price"],
                    "compare_at_price": data["compare_at_price"],
                    "image_url": data["image_url"],
                    "source_url": data["source_url"],
                    "featured": data["featured"],
                    "is_new": data["is_new"],
                    "active": data["active"],
                },
            )
            created += int(was_created)
            updated += int(not was_created)

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"Archivo válido: {len(rows)} productos."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Importación completada: {created} creados, {updated} actualizados."))

    def load_rows(self, path):
        if path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as file:
                return list(csv.DictReader(file))
        if path.suffix.lower() == ".json":
            with path.open(encoding="utf-8") as file:
                payload = json.load(file)
            if isinstance(payload, dict):
                payload = payload.get("products", [])
            if not isinstance(payload, list):
                raise CommandError("El JSON debe ser una lista o un objeto con clave 'products'.")
            return payload
        raise CommandError("Formato no soportado. Usa .csv o .json.")

    def normalize_row(self, row, index, options):
        name = self.required(row, "name", index)
        sku = self.required(row, "sku", index)
        category_name = row.get("category") or row.get("category_name") or "Catálogo"
        supplier_name = row.get("supplier") or row.get("supplier_name") or options["supplier"]
        price = self.money(row.get("price"), "price", index)
        compare_at_price = self.optional_money(row.get("compare_at_price"), "compare_at_price", index)
        incoming_description = (row.get("description") or "").strip()
        description = (
            self.build_description(name, category_name, supplier_name)
            if options["rewrite_descriptions"] or not incoming_description
            else incoming_description
        )
        return {
            "name": name,
            "sku": sku,
            "category_name": category_name.strip(),
            "supplier_name": supplier_name.strip(),
            "description": description,
            "price": price,
            "compare_at_price": compare_at_price,
            "image_url": (row.get("image_url") or "").strip(),
            "source_url": (row.get("source_url") or "").strip(),
            "featured": self.flag(row.get("featured")),
            "is_new": self.flag(row.get("is_new")),
            "active": not self.flag(row.get("inactive")),
        }

    def required(self, row, field, index):
        value = (row.get(field) or "").strip()
        if not value:
            raise CommandError(f"Fila {index}: falta '{field}'.")
        return value

    def money(self, value, field, index):
        value = (value or "").strip().replace(",", ".")
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise CommandError(f"Fila {index}: '{field}' no es un precio válido.") from exc

    def optional_money(self, value, field, index):
        if not value:
            return None
        return self.money(value, field, index)

    def flag(self, value):
        return str(value).strip().lower() in {"1", "true", "yes", "si", "sí", "x"}

    def build_description(self, name, category, supplier):
        return (
            f"{name} es una solución de {category.lower()} pensada para proyectos de cultivo que buscan "
            f"resultados constantes, instalación sencilla y buena relación calidad-precio. Seleccionado desde "
            f"{supplier}, encaja tanto en compras puntuales como en reposición profesional."
        )

