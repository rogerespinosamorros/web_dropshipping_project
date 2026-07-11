from django.contrib import admin
from django.utils.html import format_html

from .models import Brand, Category, Product, ProductVariant, Supplier, ShopSettings, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "slug"]
    list_filter = ["parent"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["parent__name", "name"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "website", "active"]
    list_filter = ["active"]
    search_fields = ["name"]


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ["sku", "attributes", "price", "pvp", "stock", "stock_level", "image_url", "active"]
    readonly_fields = ["sku", "hortitec_id"]
    show_change_link = True

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    show_change_link = True

    fields = [
        "product",
        "variant",
        "name",
        "sku",
        "quantity",
        "unit_price",
        "line_total",
    ]

    readonly_fields = [
        "product",
        "variant",
        "name",
        "sku",
        "quantity",
        "unit_price",
        "line_total",
    ]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "category", "brand", "has_variants",
        "display_price_col", "active", "featured", "outlet", "preview_image",
    ]
    list_filter = ["active", "featured", "outlet", "has_variants", "category__parent", "category"]
    search_fields = ["name", "slug", "hortitec_id"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["hortitec_id", "created_at", "updated_at", "preview_image"]
    autocomplete_fields = ["category", "brand", "supplier"]
    inlines = [ProductVariantInline]
    list_per_page = 50

    fieldsets = [
        ("Información principal", {
            "fields": ["name", "slug", "category", "brand", "supplier", "description"],
        }),
        ("Precios", {
            "fields": ["price", "pvp"],
        }),
        ("Imágenes y enlaces", {
            "fields": ["image_url", "preview_image", "source_url", "hortitec_id"],
        }),
        ("Estado", {
            "fields": ["has_variants", "active", "featured", "outlet"],
        }),
        ("Fechas", {
            "fields": ["created_at", "updated_at"],
            "classes": ["collapse"],
        }),
    ]

    @admin.display(description="precio")
    def display_price_col(self, obj):
        price = obj.display_price
        pvp = obj.display_pvp
        if pvp and pvp > price:
            return format_html(
                '<span style="color:#888;text-decoration:line-through">{} €</span> '
                '<strong>{} €</strong>',
                pvp, price,
            )
        return format_html("{} €", price)

    @admin.display(description="imagen")
    def preview_image(self, obj):
        url = obj.main_image
        if url:
            return format_html('<img src="{}" style="height:60px;object-fit:contain">', url)
        return "—"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["sku", "product", "attributes_summary", "price", "pvp", "stock", "active"]
    list_filter = ["stock", "active", "product__category"]
    search_fields = ["sku", "product__name", "hortitec_id"]
    readonly_fields = ["sku", "hortitec_id"]
    list_per_page = 100

    @admin.display(description="atributos")
    def attributes_summary(self, obj):
        items = list(obj.attributes.items())[:3]
        return " · ".join(f"{k}: {v}" for k, v in items)

@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Información general", {
            "fields": (
                "store_name",
                "contact_email",
                "phone",
            )
        }),
        ("Envíos", {
            "fields": (
                "free_shipping_from",
                "shipping_cost",
            )
        }),
        ("Impuestos", {
            "fields": (
                "vat_percentage",
            )
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "customer_name",
        "customer_email",
        "total",
        "status",
        "created_at",
    ]

    list_filter = [
        "status",
        "created_at",
    ]

    search_fields = [
        "customer_name",
        "customer_email",
    ]

    ordering = [
        "-created_at",
    ]

    inlines = [OrderItemInline]

    readonly_fields = [
        "created_at",
    ]

    fieldsets = (
        ("Cliente", {
            "fields": (
                "customer_name",
                "customer_email",
                "customer_phone",
            )
        }),

        ("Dirección de envío", {
            "fields": (
                "shipping_address",
                "shipping_city",
                "shipping_postcode",
                "shipping_country",
            )
        }),

        ("Pedido", {
            "fields": (
                "subtotal",
                "shipping_cost",
                "total",
                "status",
            )
        }),

        ("Información", {
            "fields": (
                "created_at",
            )
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = [
        "order",
        "name",
        "sku",
        "quantity",
        "unit_price",
        "line_total",
    ]

    list_filter = [
        "order",
    ]

    search_fields = [
        "name",
        "sku",
    ]

    autocomplete_fields = [
        "order",
        "product",
        "variant",
    ]