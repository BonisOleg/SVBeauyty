import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.content.models import SiteSettings

logger = logging.getLogger(__name__)


def _manager_email() -> str:
    return SiteSettings.get_solo().manager_email or settings.MANAGER_EMAIL


def _send(subject: str, template: str, context: dict, recipients: list[str]) -> None:
    recipients = [email for email in recipients if email]
    if not recipients:
        return
    body = render_to_string(template, context)
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception as exc:  # noqa: BLE001 — лист не має ламати оформлення
        logger.error("Не вдалось надіслати «%s»: %s", subject, exc)


def notify_manager_new_order(order) -> None:
    _send(
        subject=f"Нове замовлення {order.number}",
        template="commerce/emails/new_order.txt",
        context={"order": order},
        recipients=[_manager_email()],
    )


def notify_customer_new_order(order) -> None:
    if not order.email:
        return
    site = SiteSettings.get_solo()
    _send(
        subject=f"Замовлення {order.number} прийнято — {site.site_name}",
        template="commerce/emails/order_customer.txt",
        context={"order": order, "site_settings": site},
        recipients=[order.email],
    )


def notify_new_order(order) -> None:
    """Листи після оформлення: менеджеру + клієнту."""
    notify_manager_new_order(order)
    notify_customer_new_order(order)
