from decimal import Decimal

from django import template
from django.conf import settings

from apps.pricing.services import get_global_sale_state, get_price

register = template.Library()


@register.simple_tag(takes_context=True)
def variant_price(context, variant):
    request = context.get("request")
    user = request.user if request and request.user.is_authenticated else None
    return get_price(variant, user)


@register.inclusion_tag("catalog/_product_card.html", takes_context=True)
def product_card(context, product):
    request = context.get("request")
    user = request.user if request and request.user.is_authenticated else None
    variants = list(product.active_variants)
    default = product.default_variant
    global_sale = get_global_sale_state()
    variant_rows = []
    for item in variants:
        price = get_price(item, user, global_sale=global_sale)
        variant_rows.append(
            {
                "variant": item,
                "price": price,
                "selected": bool(default and item.id == default.id),
            }
        )
    return {
        "request": request,
        "user": user,
        "product": product,
        "variant": default,
        "price": get_price(default, user, global_sale=global_sale) if default else None,
        "variant_rows": variant_rows,
        "variants_count": len(variants),
        "in_wishlist": product.pk in (context.get("wishlist_product_ids") or set()),
    }


@register.inclusion_tag("catalog/_rating_stars.html")
def rating_stars(product, show_count=True):
    if not settings.REVIEWS_ENABLED:
        return {"enabled": False, "avg": 0, "count": 0, "filled": 0, "show_count": False}
    return {
        "enabled": True,
        "avg": product.rating_avg,
        "count": product.rating_count,
        "filled": product.rating_stars,
        "show_count": show_count,
    }


@register.filter
def uah(value):
    """1234.50 → '1 234,50'."""
    if value is None:
        return ""
    amount = Decimal(value).quantize(Decimal("0.01"))
    whole, _dot, cents = f"{amount:.2f}".partition(".")
    grouped = f"{int(whole):,}".replace(",", "\u00a0")
    return f"{grouped},{cents}"
