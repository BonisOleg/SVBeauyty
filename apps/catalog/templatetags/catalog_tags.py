from decimal import Decimal

from django import template

from apps.pricing.services import get_price

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
    variant = product.default_variant
    return {
        "product": product,
        "variant": variant,
        "price": get_price(variant, user) if variant else None,
        "variants_count": len(product.active_variants),
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
