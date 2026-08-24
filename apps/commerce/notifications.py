import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.content.models import SiteSettings

logger = logging.getLogger(__name__)


def _manager_email() -> str:
    return SiteSettings.get_solo().manager_email or settings.MANAGER_EMAIL


def notify_new_order(order) -> None:
    recipient = _manager_email()
    if not recipient:
        return
    body = render_to_string("commerce/emails/new_order.txt", {"order": order})
    try:
        send_mail(
            subject=f"Нове замовлення {order.number}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as exc:  # noqa: BLE001 — лист не має ламати оформлення
        logger.error("Не вдалось надіслати лист про замовлення %s: %s", order.number, exc)
