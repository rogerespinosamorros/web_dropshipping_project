import csv
import os
import tempfile

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, Supplier


class StoreViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Riego")
        supplier = Supplier.objects.create(name="Proveedor")
        cls.product = Product.objects.create(
            category=category,
            supplier=supplier,
            name="Kit de riego",
            sku="RIE-TEST",
            price="49.90",
            active=True,
            featured=True,
        )

    def test_home_and_catalog_load(self):
        self.assertEqual(self.client.get(reverse("store:home")).status_code, 200)
        response = self.client.get(reverse("store:catalog"), {"q": "riego"})
        self.assertContains(response, self.product.name)

    def test_product_detail_loads(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, self.product.sku)

    def test_product_can_be_added_to_cart(self):
        response = self.client.post(
            reverse("store:add_to_cart", args=[self.product.id]),
            {"next": reverse("store:cart")},
        )
        self.assertRedirects(response, reverse("store:cart"))
        self.assertEqual(self.client.session["cart"][str(self.product.id)], 1)


class ImportProductsCommandTests(TestCase):
    def test_import_products_creates_product_with_generated_description(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", newline="", delete=False, encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["sku", "name", "category", "supplier", "price"])
            writer.writeheader()
            writer.writerow(
                {
                    "sku": "IMP-001",
                    "name": "Maceta profesional",
                    "category": "Macetas",
                    "supplier": "Proveedor importado",
                    "price": "12.50",
                }
            )
            path = file.name

        try:
            call_command("import_products", path, rewrite_descriptions=True)
        finally:
            os.unlink(path)

        product = Product.objects.get(sku="IMP-001")
        self.assertEqual(product.category.name, "Macetas")
        self.assertIn("Maceta profesional", product.description)
