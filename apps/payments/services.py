"""Способи оплати. LiqPay підключається ключами без правок коду."""

from dataclasses import dataclass

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.commerce.models import PaymentMethod


@dataclass(frozen=True)
class PaymentOption:
    code: str
    label: str
    hint: str


def available_methods() -> list[PaymentOption]:
    options = [
        PaymentOption(
            code=PaymentMethod.BANK_DETAILS,
            label=_("Переказ на рахунок ФОП"),
            hint=_("Реквізити надішлемо після оформлення — їх можна скопіювати одним натисканням."),
        )
    ]
    if liqpay_enabled():
        options.append(
            PaymentOption(
                code=PaymentMethod.LIQPAY,
                label=_("Картка онлайн"),
                hint=_("Оплата карткою через LiqPay."),
            )
        )
    return options


def liqpay_enabled() -> bool:
    return bool(
        settings.LIQPAY_ENABLED and settings.LIQPAY_PUBLIC_KEY and settings.LIQPAY_PRIVATE_KEY
    )


def build_liqpay_payload(order):
    """Заглушка: підключення каси — окремий етап після отримання ключів ФОП."""
    if not liqpay_enabled():
        return None
    return {
        "public_key": settings.LIQPAY_PUBLIC_KEY,
        "version": "3",
        "action": "pay",
        "amount": str(order.total_uah),
        "currency": "UAH",
        "description": f"Замовлення {order.number}",
        "order_id": order.number,
    }
