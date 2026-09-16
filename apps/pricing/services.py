from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

from apps.core.utils import localized
from apps.pricing.models import PricingSettings

RETAIL = "retail"
PRO_MANUAL = "pro_manual"
PRO_AUTO = "pro_auto"
SALE = "sale"
GLOBAL_SALE = "global_sale"

CENTS = Decimal("0.01")
HUNDRED = Decimal("100")


@dataclass(frozen=True)
class PriceInfo:
    amount: Decimal
    source: str
    base_amount: Decimal

    @property
    def has_discount(self) -> bool:
        return self.amount < self.base_amount

    @property
    def is_sale(self) -> bool:
        return self.source in (SALE, GLOBAL_SALE)

    @property
    def is_pro_price(self) -> bool:
        return self.source in (PRO_MANUAL, PRO_AUTO)

    @property
    def discount_amount(self) -> Decimal:
        return (self.base_amount - self.amount) if self.has_discount else Decimal("0.00")


@dataclass(frozen=True)
class GlobalSaleState:
    is_live: bool
    percent: Decimal
    rounding_step: Decimal
    exclude_product_ids: frozenset[int]
    exclude_brand_ids: frozenset[int]

    @property
    def factor(self) -> Decimal:
        return (HUNDRED - self.percent) / HUNDRED


def is_pro(user) -> bool:
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "is_pro", False))


def round_to_step(amount, step=CENTS) -> Decimal:
    """Округлення суми до кроку (як у націнках)."""
    amount = Decimal(amount or 0)
    step = Decimal(step or CENTS)
    if step <= CENTS:
        return amount.quantize(CENTS, rounding=ROUND_HALF_UP)
    return ((amount / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step).quantize(CENTS)


def apply_markup(cost, percent, step=CENTS) -> Decimal:
    """Закупівельна + націнка, округлена до заданого кроку."""
    amount = Decimal(cost or 0) * (HUNDRED + Decimal(percent or 0)) / HUNDRED
    return round_to_step(amount, step)


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


def get_global_sale_state(settings_obj=None, *, now=None) -> GlobalSaleState:
    """Поточний стан глобальної акції (один раз на запит / цикл цін)."""
    conf = settings_obj or PricingSettings.get_solo()
    percent = Decimal(conf.global_sale_percent or 0)
    now = now or timezone.now()
    live = bool(conf.global_sale_is_active and percent > 0)
    if live and conf.global_sale_starts_at and now < conf.global_sale_starts_at:
        live = False
    if live and conf.global_sale_ends_at and now > conf.global_sale_ends_at:
        live = False
    return GlobalSaleState(
        is_live=live,
        percent=percent,
        rounding_step=Decimal(conf.rounding_step or CENTS),
        exclude_product_ids=frozenset(
            conf.global_sale_exclude_products.values_list("pk", flat=True)
        ),
        exclude_brand_ids=frozenset(conf.global_sale_exclude_brands.values_list("pk", flat=True)),
    )


def global_sale_applies(variant, state: GlobalSaleState | None = None) -> bool:
    state = state if state is not None else get_global_sale_state()
    if not state.is_live:
        return False
    product = getattr(variant, "product", None)
    if product is None:
        return False
    if product.pk in state.exclude_product_ids:
        return False
    brand_id = getattr(product, "brand_id", None)
    if brand_id is not None and brand_id in state.exclude_brand_ids:
        return False
    return True


def global_sale_amount(base: Decimal, state: GlobalSaleState) -> Decimal | None:
    """Акційна сума від роздрібної або None, якщо після округлення немає сенсу."""
    if state.percent <= 0 or base <= 0:
        return None
    amount = round_to_step(base * state.factor, state.rounding_step)
    if amount <= 0 or amount >= base:
        return None
    return amount


def sale_is_active(variant) -> bool:
    """Персональна акція варіанта: > 0 і менша за роздрібну."""
    base = Decimal(getattr(variant, "price_uah", 0) or 0)
    sale = Decimal(getattr(variant, "sale_price_uah", 0) or 0)
    return sale > 0 and sale < base


def get_price(variant, user=None, *, global_sale: GlobalSaleState | None = None) -> PriceInfo:
    """Єдине джерело ціни для вітрини, кошика й checkout."""
    base = Decimal(variant.price_uah or 0)
    if is_pro(user):
        amount = Decimal(variant.price_pro_uah or 0) or base
        source = PRO_MANUAL if variant.price_pro_is_manual else PRO_AUTO
        return PriceInfo(amount=amount, source=source, base_amount=base)

    state = global_sale if global_sale is not None else get_global_sale_state()
    if global_sale_applies(variant, state):
        amount = global_sale_amount(base, state)
        if amount is not None:
            return PriceInfo(amount=amount, source=GLOBAL_SALE, base_amount=base)

    if sale_is_active(variant):
        return PriceInfo(
            amount=Decimal(variant.sale_price_uah).quantize(CENTS),
            source=SALE,
            base_amount=base,
        )

    return PriceInfo(amount=base, source=RETAIL, base_amount=base)


def product_price_range(product, user=None, *, global_sale: GlobalSaleState | None = None):
    state = global_sale if global_sale is not None else get_global_sale_state()
    prices = [get_price(v, user, global_sale=state).amount for v in product.active_variants]
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
