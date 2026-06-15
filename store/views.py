from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category, Product


def home(request):
    return render(
        request,
        "store/home.html",
        {
            "categories": Category.objects.all()[:6],
            "featured_products": Product.objects.filter(active=True, featured=True)[:4],
            "new_products": Product.objects.filter(active=True, is_new=True)[:4],
        },
    )


def catalog(request):
    products = Product.objects.filter(active=True).select_related("category", "supplier")
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("categoria", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(sku__icontains=query))
    if category_slug:
        products = products.filter(category__slug=category_slug)
    return render(
        request,
        "store/catalog.html",
        {"products": products, "categories": Category.objects.all(), "query": query, "selected_category": category_slug},
    )


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category", "supplier"), slug=slug, active=True)
    related = Product.objects.filter(category=product.category, active=True).exclude(pk=product.pk)[:4]
    return render(request, "store/product_detail.html", {"product": product, "related": related})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, active=True)
    cart_data = request.session.get("cart", {})
    key = str(product_id)
    cart_data[key] = cart_data.get(key, 0) + 1
    request.session["cart"] = cart_data
    messages.success(request, f"{product.name} se ha añadido al carrito.")
    return redirect(request.POST.get("next", "store:cart"))


def remove_from_cart(request, product_id):
    cart_data = request.session.get("cart", {})
    cart_data.pop(str(product_id), None)
    request.session["cart"] = cart_data
    return redirect("store:cart")


def cart(request):
    cart_data = request.session.get("cart", {})
    products = Product.objects.filter(id__in=cart_data.keys())
    items = []
    subtotal = Decimal("0")
    for product in products:
        quantity = cart_data[str(product.id)]
        line_total = product.price * quantity
        subtotal += line_total
        items.append({"product": product, "quantity": quantity, "line_total": line_total})
    return render(request, "store/cart.html", {"items": items, "subtotal": subtotal})

