from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from apps.core.utils import localized
from apps.pricing.models import PricingSettings

RETAIL = "retail"
PRO_MANUAL = "pro_manual"
PRO_AUTO = "pro_auto"

CENTS = Decimal("0.01")
HUNDRED = Decimal("100")


@dataclass(frozen=True)
class PriceInfo:
    amount: Decimal
    source: str
    base_amount: Decimal

    @property
    def has_discount(self) -> bool:
        return self.source != RETAIL and self.amount < self.base_amount

    @property
    def discount_amount(self) -> Decimal:
        return (self.base_amount - self.amount) if self.has_discount else Decimal("0.00")


def is_pro(user) -> bool:
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "is_pro", False))


def apply_markup(cost, percent, step=CENTS) -> Decimal:
    """Закупівельна + націнка, округлена до заданого кроку."""
    amount = Decimal(cost or 0) * (HUNDRED + Decimal(percent or 0)) / HUNDRED
    step = Decimal(step or CENTS)
    if step <= CENTS:
        return amount.quantize(CENTS, rounding=ROUND_HALF_UP)
    return ((amount / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step).quantize(CENTS)


def apply_auto_prices(variant, settings_obj=None) -> None:
    """Перерахувати ціни, які не позначені як задані вручну."""
    conf = settings_obj or PricingSettings.get_solo()
    if not variant.price_is_manual:
        variant.price_uah = apply_markup(
            variant.purchase_price_uah, conf.retail_markup_percent, conf.rounding_step
        )
    if not variant.price_pro_is_manual:
        variant.price_pro_uah = apply_markup(
            variant.purchase_price_uah, conf.pro_markup_percent, conf.rounding_step
        )


def recalculate_all(queryset=None) -> int:
    """Масовий перерахунок автоцін. Ручні ціни лишаються недоторканими."""
    from apps.catalog.models import Variant

    conf = PricingSettings.get_solo()
    changed = []
    for variant in queryset if queryset is not None else Variant.objects.all():
        before = (variant.price_uah, variant.price_pro_uah)
        apply_auto_prices(variant, conf)
        if (variant.price_uah, variant.price_pro_uah) != before:
            changed.append(variant)
    if changed:
        Variant.objects.bulk_update(changed, ["price_uah", "price_pro_uah"])
    return len(changed)


def get_price(variant, user=None) -> PriceInfo:
    """Єдине джерело ціни для вітрини, кошика й checkout."""
    base = Decimal(variant.price_uah or 0)
    if not is_pro(user):
        return PriceInfo(amount=base, source=RETAIL, base_amount=base)

    amount = Decimal(variant.price_pro_uah or 0) or base
    source = PRO_MANUAL if variant.price_pro_is_manual else PRO_AUTO
    return PriceInfo(amount=amount, source=source, base_amount=base)


def product_price_range(product, user=None):
    prices = [get_price(v, user).amount for v in product.active_variants]
    if not prices:
        return None, None
    return min(prices), max(prices)


def delivery_note(user=None) -> str:
    settings_obj = PricingSettings.get_solo()
    field = "pro_delivery_note" if is_pro(user) else "retail_delivery_note"
    return localized(settings_obj, field)


def free_delivery_threshold(user=None):
    settings_obj = PricingSettings.get_solo()
    if is_pro(user):
        return settings_obj.free_delivery_from_pro_uah
    return settings_obj.free_delivery_from_uah


def min_order_amount(user=None):
    if is_pro(user):
        return PricingSettings.get_solo().pro_min_order_uah
    return None
