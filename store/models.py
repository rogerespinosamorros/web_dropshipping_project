from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("nombre", max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField("icono", max_length=20, default="🌿")

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField("nombre", max_length=120)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    active = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, related_name="products", on_delete=models.PROTECT)
    name = models.CharField("nombre", max_length=180)
    slug = models.SlugField(unique=True, blank=True)
    sku = models.CharField("SKU", max_length=50, unique=True)
    description = models.TextField("descripción", blank=True)
    price = models.DecimalField("precio", max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        "precio anterior", max_digits=10, decimal_places=2, blank=True, null=True
    )
    image_url = models.URLField("URL de imagen", blank=True)
    source_url = models.URLField("URL de origen", blank=True)
    featured = models.BooleanField("destacado", default=False)
    is_new = models.BooleanField("nuevo", default=False)
    active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    @property
    def has_discount(self):
        return self.compare_at_price and self.compare_at_price > self.price

    def __str__(self):
        return self.name
