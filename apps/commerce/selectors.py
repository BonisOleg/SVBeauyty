from apps.commerce import services
from apps.commerce.models import Order


def get_active_cart(request, *, create: bool = False):
    return services.get_cart(request, create=create)


def cart_summary_for(request):
    user = request.user if request.user.is_authenticated else None
    return services.cart_summary(get_active_cart(request, create=False), user)


def order_for_user(number: str, user):
    return Order.objects.prefetch_related("items").filter(number=number, user=user).first()
