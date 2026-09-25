import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.urls import reverse

from apps.content.models import SiteSettings

logger = logging.getLogger(__name__)

THROTTLE_SECONDS = 300


def notify_new_message(message) -> None:
    """Один лист на діалог не частіше ніж раз на 5 хвилин."""
    recipient = SiteSettings.get_solo().manager_email or settings.MANAGER_EMAIL
    if not recipient:
        return

    cache_key = f"chat_notify_{message.session_id}"
    if cache.get(cache_key):
        return
    cache.set(cache_key, True, THROTTLE_SECONDS)

    session = message.session
    body = (
        f"Нове повідомлення в чаті сайту.\n\n"
        f"Клієнт: {session.name or '—'}\n"
        f"Телефон: {session.phone or '—'}\n"
        f"Текст: {message.text or '—'}\n"
        f"Вкладення: {message.attachments.count()}\n\n"
        f"Відповісти в адмінці: {reverse('admin:chat_chatsession_change', args=[session.pk])}"
    )
    try:
        send_mail(
            subject=f"Чат SVbeauty: {session.name or 'новий клієнт'}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as exc:  # noqa: BLE001 — лист не має ламати чат
        logger.error("Не вдалось надіслати лист про чат #%s: %s", session.pk, exc)
