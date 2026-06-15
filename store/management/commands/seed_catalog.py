from decimal import Decimal

from django.core.management.base import BaseCommand

from store.models import Category, Product, Supplier


class Command(BaseCommand):
    help = "Crea un catálogo demo para desarrollo."

    def handle(self, *args, **options):
        supplier, _ = Supplier.objects.get_or_create(name="Proveedor demo", email="ventas@proveedor.example")
        catalog = {
            "Riego inteligente": [
                ("Kit de riego automático", "RIE-001", "89.90", True),
                ("Programador WiFi", "RIE-002", "54.90", False),
            ],
            "Cultivo urbano": [
                ("Huerto vertical modular", "CUL-001", "129.00", True),
                ("Mesa de cultivo compacta", "CUL-002", "99.00", False),
            ],
            "Iluminación": [
                ("Lámpara LED espectro completo", "LED-001", "74.90", True),
                ("Barra LED para semilleros", "LED-002", "39.90", False),
            ],
        }
        for category_name, products in catalog.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for name, sku, price, featured in products:
                Product.objects.get_or_create(
                    sku=sku,
                    defaults={
                        "name": name,
                        "category": category,
                        "supplier": supplier,
                        "description": "Producto seleccionado para cultivar de forma sencilla, eficiente y responsable.",
                        "price": Decimal(price),
                        "featured": featured,
                        "is_new": True,
                    },
                )
        self.stdout.write(self.style.SUCCESS("Catálogo demo creado."))

