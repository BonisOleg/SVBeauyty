from apps.commerce.services import cart_summary, get_cart


def cart_context(request):
    if request.path.startswith(("/admin/", "/static/", "/media/")):
        return {}
    cart = get_cart(request, create=False)
    user = request.user if request.user.is_authenticated else None
    summary = cart_summary(cart, user)
    return {"cart_count": summary["count"], "cart_subtotal": summary["subtotal"]}
