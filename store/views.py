from decimal import Decimal
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count, Q
from django.db import transaction
from django.http import request
from django.shortcuts import get_object_or_404, redirect, render
from urllib.parse import urlencode
from .forms import CheckoutForm
from .models import Category, Product, ProductVariant, Brand, Order, OrderItem, MainCategory
from .emails import send_order_confirmation
from .services.orders import create_order_from_checkout
from .services.cart import (build_cart, calculate_total,)



def home(request):
    return render(
        request,
        "store/home.html",
        {
            "categories": Category.objects.filter(
                parent=None,
                show_on_home=True,
            ).order_by(
                "home_order",
                "name",
            ),
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
    main_slug = request.GET.get("main", "").strip()
    min_price = request.GET.get("precio_min", "").strip()
    max_price = request.GET.get("precio_max", "").strip()
    sort = request.GET.get("sort", "").strip()
    brand_slug = request.GET.get("marca", "").strip()

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

    if main_slug:
        products = products.filter(
            category__main_category__slug=main_slug
        )   

    if brand_slug:
        products = products.filter(brand__slug=brand_slug)

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

    # Ordenación
    if sort == "price_asc":
        products = products.order_by("price", "name")

    elif sort == "price_desc":
        products = products.order_by("-price", "name")

    elif sort == "name_asc":
        products = products.order_by("name")

    elif sort == "name_desc":
        products = products.order_by("-name")

    else:
    # Orden por defecto
        products = products.order_by("name")

    # Categorías padre para el menú lateral
    categories = Category.objects.filter(parent=None).prefetch_related("children")

    # Paginación
    paginator = Paginator(products, 24)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = (
        Category.objects
        .filter(parent=None)
        .annotate(
            product_count=Count(
                "products",
                filter=Q(products__active=True),
                distinct=True,
            )
        )
        .prefetch_related("children")
    )

    main_categories = (
        MainCategory.objects
        .filter(active=True)
        .order_by("order")
    )

    selected_main = None
    subcategories = Category.objects.none()

    if main_slug:

        selected_main = MainCategory.objects.filter(
            slug=main_slug
        ).first()

        if selected_main:

            subcategories = (
                Category.objects
                .filter(main_category=selected_main)
                .order_by("name")
            )

    params = request.GET.copy()
    params.pop("page", None)

    querystring = urlencode(params)

    brands = (
    Brand.objects
    .annotate(
        product_count=Count(
            "products",
            filter=Q(products__active=True),
            distinct=True,
        )
    )
    .filter(product_count__gt=0)
    .order_by("name")
)

    return render(
        request,
        "store/catalog.html",
        {
            "products": page_obj,
            "categories": categories,
            "main_categories": main_categories,
            "query": query,
            "selected_category": category_slug,
            "selected_main": main_slug,
            "selected_main_category": selected_main,
            "subcategories": subcategories,
            "min_price": min_price,
            "max_price": max_price,
            "page_obj": page_obj,
            "sort": sort,
            "querystring": querystring,
            "brands": brands,
            "selected_brand": brand_slug,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects
        .select_related(
            "category",
            "category__parent",
            "brand",
            "supplier",
        )
        .prefetch_related("variants"),
        slug=slug,
        active=True,
    )

    variants = (
        product.variants
        .filter(active=True)
        .order_by("price")
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
        {
            "product": product,
            "variants": variants,
            "related": related,
        },
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

    # Limpiar entradas inválidas
    valid_entries = [
        entry for entry in cart_data.values()
        if isinstance(entry, dict) and entry.get("product_id")
    ]

    product_ids = list({
        entry["product_id"]
        for entry in valid_entries
    })

    # Una única consulta para todos los productos
    products = (
        Product.objects
        .filter(pk__in=product_ids, active=True)
        .select_related("brand")
        .prefetch_related("variants")
    )

    products_by_id = {
        product.id: product
        for product in products
    }

    items = []
    subtotal = Decimal("0")

    for key, entry in cart_data.items():

        if not isinstance(entry, dict):
            continue

        product = products_by_id.get(entry.get("product_id"))

        if product is None:
            continue

        qty = entry.get("qty", 1)
        variant = None

        if entry.get("variant_id"):

            variant = next(
                (
                    v for v in product.variants.all()
                    if v.id == entry["variant_id"]
                ),
                None,
            )

            if variant is None:
                continue

            unit_price = variant.price
            label = str(variant)

        else:

            unit_price = product.display_price
            label = product.name

        line_total = unit_price * qty
        subtotal += line_total

        items.append(
            {
                "key": key,
                "product": product,
                "variant": variant,
                "label": label,
                "unit_price": unit_price,
                "qty": qty,
                "line_total": line_total,
            }
        )

    return render(
        request,
        "store/cart.html",
        {
            "items": items,
            "subtotal": subtotal,
        },
    )


def checkout(request):

    items, subtotal = build_cart(request)

    if not items:
        messages.warning(request, "Tu carrito está vacío.")
        return redirect("store:cart")

    shipping, total = calculate_total(subtotal)

    if request.method == "POST":

        form = CheckoutForm(request.POST)

        if form.is_valid():

            order = create_order_from_checkout(
                request=request,
                form=form,
                items=items,
                subtotal=subtotal,
                shipping=shipping,
                total=total,
            )

            request.session["cart"] = {}
            request.session.modified = True

            send_order_confirmation(order)

            messages.success(
                request,
                "Pedido creado correctamente."
            )

            return redirect(
                "store:order_success",
                order_id=order.id,
            )

    else:

        form = CheckoutForm()

    return render(
        request,
        "store/checkout.html",
        {
            "form": form,
            "items": items,
            "subtotal": subtotal,
            "shipping": shipping,
            "total": total,
        },
    )
    

def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        pk=order_id,
    )

    return render(
        request,
        "store/order_success.html",
        {
            "order": order,
        },
    )  