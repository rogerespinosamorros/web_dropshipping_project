from django.contrib import admin

from .models import Category, Product, Supplier


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "supplier", "price", "active")
    list_filter = ("active", "featured", "is_new", "category", "supplier")
    search_fields = ("name", "sku", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Supplier)

