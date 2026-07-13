from decimal import Decimal

from store.models import Product, ShopSettings

def build_cart(request):
    """
    Construye el carrito a partir de la sesión.
    Devuelve:
        items
        subtotal
    """

    cart_data = request.session.get("cart", {})

    valid_entries = [
        entry
        for entry in cart_data.values()
        if isinstance(entry, dict) and entry.get("product_id")
    ]

    product_ids = list({
        entry["product_id"]
        for entry in valid_entries
    })

    products = (
        Product.objects
        .filter(
            pk__in=product_ids,
            active=True,
        )
        .prefetch_related("variants")
    )

    products_by_id = {
        product.id: product
        for product in products
    }

    items = []
    subtotal = Decimal("0")

    for entry in cart_data.values():

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
                    v
                    for v in product.variants.all()
                    if v.id == entry["variant_id"]
                ),
                None,
            )

            if variant is None:
                continue

            unit_price = variant.price

        else:

            unit_price = product.display_price

        line_total = unit_price * qty

        subtotal += line_total

        items.append({
            "product": product,
            "variant": variant,
            "qty": qty,
            "line_total": line_total,
        })

    return items, subtotal




def calculate_shipping(subtotal):

    settings = ShopSettings.load()

    if subtotal >= settings.free_shipping_from:
        return Decimal("0")

    return settings.shipping_cost


def calculate_total(subtotal):

    shipping = calculate_shipping(subtotal)

    total = subtotal + shipping

    return shipping, total