from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("nombre", max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
        verbose_name="categoría padre",
    )
    icon = models.CharField("icono", max_length=20, default="🌿")

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} › {self.name}"
        return self.name

    @property
    def full_path(self):
        return str(self)


class Brand(models.Model):
    name = models.CharField("nombre", max_length=120)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "marca"
        verbose_name_plural = "marcas"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Brand.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
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
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.PROTECT, verbose_name="categoría"
    )
    brand = models.ForeignKey(
        Brand,
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="marca",
    )
    supplier = models.ForeignKey(
        Supplier, related_name="products", on_delete=models.PROTECT, verbose_name="proveedor"
    )
    name = models.CharField("nombre", max_length=220)
    slug = models.SlugField(max_length=260, unique=True, blank=True)
    description = models.TextField("descripción", blank=True)

    # Precio base (precio de compra del producto simple o de la variante por defecto)
    # Para productos con variantes, el precio real vive en ProductVariant.
    # Este campo sirve para búsquedas/filtros de precio y para productos sin variante.
    price = models.DecimalField("precio compra", max_digits=10, decimal_places=2)
    pvp = models.DecimalField("PVP", max_digits=10, decimal_places=2, null=True, blank=True)

    image_url = models.URLField("imagen principal", blank=True, max_length=500)
    source_url = models.URLField("URL en Hortitec", blank=True, max_length=500)
    hortitec_id = models.CharField("ID Hortitec", max_length=30, blank=True, db_index=True)

    has_variants = models.BooleanField("tiene variantes", default=False)
    featured = models.BooleanField("destacado", default=False)
    outlet = models.BooleanField("outlet", default=False)
    active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    @property
    def display_price(self):
        """Precio de la variante más barata o del producto simple."""
        if self.has_variants:
            cheapest = self.variants.filter(active=True).order_by("price").first()
            return cheapest.price if cheapest else self.price
        return self.price

    @property
    def display_pvp(self):
        if self.has_variants:
            cheapest = self.variants.filter(active=True).order_by("price").first()
            return cheapest.pvp if cheapest else self.pvp
        return self.pvp

    @property
    def has_discount(self):
        pvp = self.display_pvp
        return pvp and pvp > self.display_price

    @property
    def main_image(self):
        if self.has_variants:
            v = self.variants.filter(active=True).exclude(image_url="").first()
            if v:
                return v.image_url
        return self.image_url

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE, verbose_name="producto"
    )
    sku = models.CharField("SKU", max_length=50, unique=True)
    hortitec_id = models.CharField("ID Hortitec", max_length=30, blank=True, db_index=True)

    # Atributos de la variante almacenados como JSON
    # Ejemplo: {"capacidad": "11 l", "color": "Negro"}
    attributes = models.JSONField("atributos", default=dict, blank=True)

    price = models.DecimalField("precio compra", max_digits=10, decimal_places=2)
    pvp = models.DecimalField("PVP", max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.URLField("imagen", blank=True, max_length=500)
    stock = models.BooleanField("en stock", default=True)
    stock_level = models.CharField("nivel stock", max_length=30, blank=True)
    active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "variante"
        verbose_name_plural = "variantes"
        ordering = ["price"]

    @property
    def has_discount(self):
        return self.pvp and self.pvp > self.price

    @property
    def display_attributes(self):
        """Devuelve los atributos como lista de (clave_legible, valor)."""
        return [(k.replace("-", " ").title(), v) for k, v in self.attributes.items()]

    def __str__(self):
        attrs = ", ".join(f"{k}: {v}" for k, v in self.attributes.items())
        return f"{self.product.name} — {attrs}" if attrs else f"{self.product.name} ({self.sku})"
