def cart_count(request):
    cart = request.session.get("cart", {})

    total = 0

    for item in cart.values():

        if isinstance(item, dict):
            total += item.get("qty", 0)

        else:
            # Compatibilidad con el formato antiguo
            total += item

    return {
        "cart_count": total
    }