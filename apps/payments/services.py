"""Способи оплати. LiqPay підключається ключами без правок коду."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.commerce.models import PaymentMethod

LIQPAY_CHECKOUT_URL = "https://www.liqpay.ua/api/3/checkout"


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


def build_liqpay_payload(order) -> dict | None:
    """Дані форми LiqPay Checkout. З фейковими ключами кнопка є, оплата не пройде."""
    if not liqpay_enabled():
        return None

    params = {
        "public_key": settings.LIQPAY_PUBLIC_KEY,
        "version": "3",
        "action": "pay",
        "amount": str(order.total_uah),
        "currency": "UAH",
        "description": f"Замовлення {order.number}",
        "order_id": order.number,
    }
    data = base64.b64encode(json.dumps(params, ensure_ascii=False).encode("utf-8")).decode("ascii")
    sign_raw = f"{settings.LIQPAY_PRIVATE_KEY}{data}{settings.LIQPAY_PRIVATE_KEY}".encode("utf-8")
    signature = base64.b64encode(hashlib.sha1(sign_raw).digest()).decode("ascii")
    return {
        "checkout_url": LIQPAY_CHECKOUT_URL,
        "data": data,
        "signature": signature,
        "amount": params["amount"],
        "order_id": params["order_id"],
    }
