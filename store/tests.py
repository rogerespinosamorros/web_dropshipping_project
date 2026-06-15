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

