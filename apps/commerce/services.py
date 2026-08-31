from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.translation import get_language, gettext as _

from apps.catalog.models import Variant
from apps.commerce.models import (
    Cart,
    CartItem,
    CartStatus,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusLog,
    PaymentMethod,
)
from apps.content.models import SiteSettings
from apps.loyalty import services as loyalty
from apps.loyalty.models import LoyaltySettings
from apps.pricing.services import get_price

MAX_QTY = 99


class CartError(Exception):
    """Бізнес-помилка кошика/checkout (залишок, порожній кошик тощо)."""


def _ensure_session(request) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_cart(request, create: bool = True) -> Cart | None:
    session_key = _ensure_session(request)
    user = request.user if request.user.is_authenticated else None

    cart = None
    if user:
        cart = Cart.objects.filter(user=user, status=CartStatus.ACTIVE).order_by("-updated_at").first()
    if cart is None:
        cart = (
            Cart.objects.filter(session_key=session_key, user__isnull=True, status=CartStatus.ACTIVE)
            .order_by("-updated_at")
            .first()
        )
        if cart and user:
            cart.user = user
            cart.save(update_fields=["user", "updated_at"])

    if cart is None and create:
        cart = Cart.objects.create(session_key=session_key, user=user)
    return cart


def add_item(cart: Cart, variant, quantity: int = 1) -> CartItem:
    quantity = max(1, min(MAX_QTY, int(quantity)))
    if not variant.is_active or variant.stock_qty < 1:
        raise CartError(_("Товару немає в наявності."))

    item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={"quantity": 0})
    new_qty = min(MAX_QTY, (0 if created else item.quantity) + quantity, variant.stock_qty)
    if new_qty < 1:
        raise CartError(_("Недостатньо товару на складі."))
    item.quantity = new_qty
    item.save(update_fields=["quantity", "updated_at"])
    cart.save(update_fields=["updated_at"])
    return item


def set_quantity(cart: Cart, item_id: int, quantity: int) -> None:
    item = CartItem.objects.select_related("variant").filter(cart=cart, pk=item_id).first()
    if not item:
        return
    quantity = int(quantity)
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = min(MAX_QTY, quantity, item.variant.stock_qty)
        if item.quantity < 1:
            item.delete()
        else:
            item.save(update_fields=["quantity", "updated_at"])
    cart.save(update_fields=["updated_at"])


def remove_item(cart: Cart, item_id: int) -> None:
    CartItem.objects.filter(cart=cart, pk=item_id).delete()
    cart.save(update_fields=["updated_at"])


def cart_rows(cart: Cart | None, user=None) -> list[dict]:
    if cart is None:
        return []
    items = cart.items.select_related("variant__product__brand").order_by("id")
    rows = []
    for item in items:
        price = get_price(item.variant, user)
        rows.append(
            {
                "item": item,
                "variant": item.variant,
                "product": item.variant.product,
                "price": price,
                "line_total": (price.amount * item.quantity).quantize(Decimal("0.01")),
            }
        )
    return rows


def cart_summary(cart: Cart | None, user=None) -> dict:
    rows = cart_rows(cart, user)
    subtotal = sum((row["line_total"] for row in rows), Decimal("0.00"))
    return {
        "rows": rows,
        "count": sum(row["item"].quantity for row in rows),
        "subtotal": subtotal,
        "saved": sum((row["price"].discount_amount * row["item"].quantity for row in rows), Decimal("0.00")),
    }


def generate_order_number() -> str:
    today = timezone.localdate()
    prefix = f"SV-{today:%d%m%y}-"
    last = Order.objects.filter(number__startswith=prefix).order_by("-number").first()
    seq = int(last.number.rsplit("-", 1)[1]) + 1 if last else 1
    return f"{prefix}{seq:04d}"


@transaction.atomic
def create_order(request, cart: Cart, data: dict, redeem_points: int = 0) -> Order:
    user = request.user if request.user.is_authenticated else None
    cart_items = list(
        cart.items.select_related("variant__product__brand").select_for_update().order_by("id")
    )
    if not cart_items:
        raise CartError(_("Кошик порожній."))

    locked_variants = {
        v.pk: v
        for v in Variant.objects.select_for_update().filter(
            pk__in=[item.variant_id for item in cart_items], is_active=True
        )
    }

    rows = []
    for item in cart_items:
        variant = locked_variants.get(item.variant_id)
        if variant is None or variant.stock_qty < item.quantity:
            raise CartError(_("Недостатньо товару на складі. Оновіть кошик."))
        price = get_price(variant, user)
        rows.append(
            {
                "item": item,
                "variant": variant,
                "price": price,
                "line_total": (price.amount * item.quantity).quantize(Decimal("0.01")),
            }
        )

    subtotal = sum((row["line_total"] for row in rows), Decimal("0.00"))
    redeem_points = max(0, min(int(redeem_points or 0), loyalty.max_redeemable_points(user, subtotal)))
    discount = loyalty.points_to_uah(redeem_points) if redeem_points else Decimal("0.00")

    order = Order.objects.create(
        number=generate_order_number(),
        user=user,
        client_type=getattr(user, "client_type", "regular") if user else "regular",
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data["phone"],
        email=data.get("email", ""),
        other_recipient=bool(data.get("other_recipient")),
        recipient_first_name=(data.get("recipient_first_name") or "").strip(),
        recipient_last_name=(data.get("recipient_last_name") or "").strip(),
        recipient_phone=(data.get("recipient_phone") or "").strip(),
        delivery_method=data.get("delivery_method", "nova_poshta"),
        delivery_city=data.get("delivery_city", ""),
        delivery_city_ref=data.get("delivery_city_ref", ""),
        delivery_branch=data.get("delivery_branch", ""),
        delivery_branch_ref=data.get("delivery_branch_ref", ""),
        delivery_address=data.get("delivery_address", ""),
        payment_method=data["payment_method"],
        status=_initial_status_for_payment(data["payment_method"]),
        comment=data.get("comment", ""),
        gdpr_accepted=bool(data.get("gdpr_accepted")),
        locale=(get_language() or "uk")[:2],
        subtotal_uah=subtotal,
        loyalty_spent_points=redeem_points,
        loyalty_discount_uah=discount,
        total_uah=max(Decimal("0.00"), subtotal - discount),
    )
    order.bank_details_snapshot = SiteSettings.get_solo().bank_details(order.number)
    order.save(update_fields=["bank_details_snapshot", "updated_at"])

    for row in rows:
        variant = row["variant"]
        qty = row["item"].quantity
        updated = Variant.objects.filter(pk=variant.pk, stock_qty__gte=qty).update(
            stock_qty=F("stock_qty") - qty
        )
        if not updated:
            raise CartError(_("Недостатньо товару на складі. Оновіть кошик."))
        OrderItem.objects.create(
            order=order,
            variant=variant,
            product_name=variant.product.name_uk,
            sku=variant.sku,
            volume=variant.volume,
            unit_price_uah=row["price"].amount,
            unit_purchase_price_uah=variant.purchase_price_uah,
            price_source=row["price"].source,
            quantity=qty,
        )

    if redeem_points and user:
        loyalty.redeem_for_order(user, order, redeem_points)
    if user and LoyaltySettings.get_solo().is_enabled:
        loyalty.earn_for_order(order)

    OrderStatusLog.objects.create(order=order, old_status="", new_status=order.status, changed_by=user)

    cart.status = CartStatus.CONVERTED
    cart.save(update_fields=["status", "updated_at"])
    return order


def _initial_status_for_payment(payment_method: str) -> str:
    """До підтвердження оплати (банк / LiqPay) — «Очікує оплати»."""
    if payment_method in {PaymentMethod.BANK_DETAILS, PaymentMethod.LIQPAY}:
        return OrderStatus.AWAITING_PAYMENT
    return OrderStatus.NEW


@transaction.atomic
def set_order_status(order: Order, new_status: str, *, changed_by=None) -> Order:
    old = order.status
    if old == new_status:
        return order
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])
    OrderStatusLog.objects.create(
        order=order,
        old_status=old,
        new_status=new_status,
        changed_by=changed_by if getattr(changed_by, "is_authenticated", False) else None,
    )
    return order


def mark_order_paid(order: Order, *, changed_by=None) -> Order:
    """Успішна оплата (LiqPay callback або ручне підтвердження)."""
    return set_order_status(order, OrderStatus.PAID, changed_by=changed_by)


def mark_order_awaiting_payment(order: Order, *, changed_by=None) -> Order:
    """Помилка / скасування онлайн-оплати."""
    return set_order_status(order, OrderStatus.AWAITING_PAYMENT, changed_by=changed_by)
