from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category, Product, ProductVariant


def home(request):
    return render(
        request,
        "store/home.html",
        {
            "categories": Category.objects.filter(parent=None)[:6],
            "featured_products": (
                Product.objects
                .filter(active=True, featured=True)
                .select_related("category", "brand")
                .prefetch_related("variants")[:8]
            ),
        },
    )


def catalog(request):
    products = (
        Product.objects
        .filter(active=True)
        .select_related("category", "category__parent", "brand")
        .prefetch_related("variants")
    )

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("categoria", "").strip()
    min_price = request.GET.get("precio_min", "").strip()
    max_price = request.GET.get("precio_max", "").strip()

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(variants__sku__icontains=query)
        ).distinct()

    if category_slug:
        products = products.filter(
            Q(category__slug=category_slug) | Q(category__parent__slug=category_slug)
        )

    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except Exception:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

    # Categorías padre para el menú lateral
    categories = Category.objects.filter(parent=None).prefetch_related("children")

    return render(
        request,
        "store/catalog.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "selected_category": category_slug,
            "min_price": min_price,
            "max_price": max_price,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects
        .select_related("category", "category__parent", "brand", "supplier")
        .prefetch_related("variants"),
        slug=slug,
        active=True,
    )
    related = (
        Product.objects
        .filter(category=product.category, active=True)
        .exclude(pk=product.pk)
        .select_related("brand")
        .prefetch_related("variants")[:4]
    )
    return render(
        request,
        "store/product_detail.html",
        {"product": product, "related": related},
    )


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, active=True)

    # Si el producto tiene variantes, esperamos variant_id en el POST
    variant_id = request.POST.get("variant_id")
    cart_data = request.session.get("cart", {})

    if product.has_variants and variant_id:
        key = f"p{product_id}_v{variant_id}"
        variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)
        cart_data[key] = {
            "product_id": product_id,
            "variant_id": int(variant_id),
            "qty": cart_data.get(key, {}).get("qty", 0) + 1 if isinstance(cart_data.get(key), dict) else 1,
        }
        messages.success(request, f"{product.name} ({variant}) añadido al carrito.")
    else:
        key = f"p{product_id}"
        entry = cart_data.get(key, {})
        cart_data[key] = {
            "product_id": product_id,
            "variant_id": None,
            "qty": (entry.get("qty", 0) if isinstance(entry, dict) else 0) + 1,
        }
        messages.success(request, f"{product.name} añadido al carrito.")

    request.session["cart"] = cart_data
    return redirect(request.POST.get("next", "store:cart"))


def remove_from_cart(request, key):
    cart_data = request.session.get("cart", {})
    cart_data.pop(key, None)
    request.session["cart"] = cart_data
    return redirect("store:cart")


def cart(request):
    cart_data = request.session.get("cart", {})
    items = []
    subtotal = Decimal("0")

    for key, entry in cart_data.items():
        if not isinstance(entry, dict):
            continue

        product_id = entry.get("product_id")
        variant_id = entry.get("variant_id")
        qty = entry.get("qty", 1)

        try:
            product = Product.objects.select_related("brand").get(pk=product_id, active=True)
        except Product.DoesNotExist:
            continue

        if variant_id:
            try:
                variant = ProductVariant.objects.get(pk=variant_id, product=product)
                unit_price = variant.price
                label = str(variant)
            except ProductVariant.DoesNotExist:
                continue
        else:
            variant = None
            unit_price = product.display_price
            label = product.name

        line_total = unit_price * qty
        subtotal += line_total
        items.append({
            "key": key,
            "product": product,
            "variant": variant,
            "label": label,
            "unit_price": unit_price,
            "qty": qty,
            "line_total": line_total,
        })

    return render(request, "store/cart.html", {"items": items, "subtotal": subtotal})
