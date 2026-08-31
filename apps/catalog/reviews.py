from apps.commerce.models import OrderItem, OrderStatus

VERIFIED_ORDER_STATUSES = (
    OrderStatus.PAID,
    OrderStatus.SHIPPED,
    OrderStatus.DONE,
)


def user_purchased_product(user, product) -> bool:
    """Чи є в користувача оплачене/виконане замовлення з цим товаром."""
    if not user or not getattr(user, "is_authenticated", False) or not getattr(user, "pk", None):
        return False
    return OrderItem.objects.filter(
        order__user_id=user.pk,
        order__status__in=VERIFIED_ORDER_STATUSES,
        variant__product_id=product.pk,
    ).exists()
