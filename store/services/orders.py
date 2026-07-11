from django.db import transaction

from store.models import Order, OrderItem


def create_order_from_checkout(
    request,
    form,
    items,
    subtotal,
    shipping,
    total,
):
    """
    Crea un pedido y todas sus líneas.
    Devuelve el objeto Order.
    """

    with transaction.atomic():

        order = Order.objects.create(

            user=request.user if request.user.is_authenticated else None,

            customer_name=form.cleaned_data["customer_name"],
            customer_email=form.cleaned_data["customer_email"],
            customer_phone=form.cleaned_data["customer_phone"],

            shipping_address=form.cleaned_data["shipping_address"],
            shipping_city=form.cleaned_data["shipping_city"],
            shipping_postcode=form.cleaned_data["shipping_postcode"],
            shipping_country=form.cleaned_data["shipping_country"],

            subtotal=subtotal,
            shipping_cost=shipping,
            total=total,
        )

        for item in items:

            OrderItem.objects.create(

                order=order,

                product=item["product"],

                variant=item["variant"],

                name=item["product"].name,

                sku=(
                    item["variant"].sku
                    if item["variant"]
                    else item["product"].hortitec_id
                ),

                unit_price=(
                    item["variant"].price
                    if item["variant"]
                    else item["product"].display_price
                ),

                quantity=item["qty"],

                line_total=item["line_total"],
            )

    return order