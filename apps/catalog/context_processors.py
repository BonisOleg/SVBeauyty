from apps.catalog import wishlist as wishlist_services


def wishlist_context(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"wishlist_count": 0, "wishlist_product_ids": set()}
    ids = wishlist_services.product_ids_for(user)
    return {"wishlist_count": len(ids), "wishlist_product_ids": ids}
