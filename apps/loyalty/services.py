from datetime import timedelta
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from apps.loyalty.models import LoyaltyAccount, LoyaltySettings, LoyaltyTransaction, TransactionKind

CENTS = Decimal("0.01")


def get_account(user) -> LoyaltyAccount | None:
    if not getattr(user, "is_authenticated", False):
        return None
    account, _created = LoyaltyAccount.objects.get_or_create(user=user)
    return account


def get_balance(user) -> int:
    account = get_account(user)
    return account.balance if account else 0


def pending_earn_points(user) -> int:
    """Бали за покупки, які ще в холді (недоступні до списання)."""
    return sum(item["points"] for item in pending_earn_releases(user))


def pending_earn_releases(user) -> list[dict]:
    """Нарахування в холді з датою, коли стануть доступні до списання."""
    account = get_account(user)
    if account is None:
        return []
    conf = LoyaltySettings.get_solo()
    hold_days = int(conf.earn_hold_days or 0)
    if hold_days <= 0:
        return []
    since = timezone.now() - timedelta(days=hold_days)
    rows = []
    for txn in account.transactions.filter(
        kind=TransactionKind.EARN, points__gt=0, created_at__gt=since
    ).order_by("created_at"):
        rows.append(
            {
                "points": int(txn.points),
                "created_at": txn.created_at,
                "available_at": txn.created_at + timedelta(days=hold_days),
                "order": txn.order,
            }
        )
    return rows


def get_available_balance(user) -> int:
    """Баланс, доступний до списання зараз (мінус холд на нарахування з покупок)."""
    return max(0, get_balance(user) - pending_earn_points(user))


def points_to_uah(points: int) -> Decimal:
    rate = LoyaltySettings.get_solo().redeem_uah_per_point or Decimal("0")
    return (Decimal(points) * Decimal(rate)).quantize(CENTS, rounding=ROUND_HALF_UP)


def max_redeemable_points(user, subtotal: Decimal) -> int:
    """Скільки балів реально можна списати з цієї суми."""
    conf = LoyaltySettings.get_solo()
    if not conf.is_enabled:
        return 0
    balance = get_available_balance(user)
    if balance <= 0 or subtotal <= 0:
        return 0
    rate = Decimal(conf.redeem_uah_per_point or 0)
    if rate <= 0:
        return 0
    limit_uah = (Decimal(subtotal) * Decimal(conf.max_redeem_percent) / Decimal("100")).quantize(
        CENTS, rounding=ROUND_DOWN
    )
    limit_points = int((limit_uah / rate).to_integral_value(rounding=ROUND_DOWN))
    return max(0, min(balance, limit_points))


def calculate_earn(order) -> int:
    conf = LoyaltySettings.get_solo()
    if not conf.is_enabled or not order.user:
        return 0
    if order.user.is_pro and not conf.earn_for_pro:
        return 0
    rate = Decimal(conf.earn_points_per_uah or 0)
    if rate <= 0:
        return 0
    return int((Decimal(order.total_uah) * rate).to_integral_value(rounding=ROUND_DOWN))


@transaction.atomic
def apply_transaction(user, kind: str, points: int, order=None, comment: str = "") -> LoyaltyTransaction | None:
    """Атомарна зміна балансу. points: + нарахування, − списання."""
    if points == 0 or not getattr(user, "is_authenticated", False):
        return None

    LoyaltyAccount.objects.get_or_create(user=user)
    account = LoyaltyAccount.objects.select_for_update().get(user=user)

    if points < 0 and account.balance + points < 0:
        raise ValueError("Недостатньо балів на рахунку")

    if order is not None and LoyaltyTransaction.objects.filter(order=order, kind=kind).exists():
        return None

    account.balance += points
    account.save(update_fields=["balance", "updated_at"])

    return LoyaltyTransaction.objects.create(
        account=account,
        order=order,
        kind=kind,
        points=points,
        balance_after=account.balance,
        comment=comment,
    )


def redeem_for_order(user, order, points: int):
    return apply_transaction(
        user, TransactionKind.REDEEM, -abs(points), order=order, comment=f"Замовлення {order.number}"
    )


def earn_for_order(order):
    points = calculate_earn(order)
    if points <= 0:
        return None
    return apply_transaction(
        order.user, TransactionKind.EARN, points, order=order, comment=f"Замовлення {order.number}"
    )
