from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class ChatSession(TimeStampedModel):
    session_key = models.CharField(_("Ключ сесії"), max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_sessions",
        verbose_name=_("Клієнт"),
    )
    name = models.CharField(_("Ім'я"), max_length=120, blank=True)
    phone = models.CharField(_("Телефон"), max_length=32, blank=True)
    is_closed = models.BooleanField(_("Закрито"), default=False)

    class Meta:
        verbose_name = _("Діалог")
        verbose_name_plural = _("Діалоги")
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name or f"Діалог #{self.pk}"

    @property
    def unread_count(self) -> int:
        return self.messages.filter(author=MessageAuthor.CUSTOMER, is_read=False).count()


class MessageAuthor(models.TextChoices):
    CUSTOMER = "customer", _("Клієнт")
    MANAGER = "manager", _("Менеджер")


class ChatMessage(TimeStampedModel):
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages", verbose_name=_("Діалог")
    )
    author = models.CharField(_("Автор"), max_length=10, choices=MessageAuthor.choices)
    text = models.TextField(_("Повідомлення"))
    is_read = models.BooleanField(_("Прочитано"), default=False)

    class Meta:
        verbose_name = _("Повідомлення")
        verbose_name_plural = _("Повідомлення")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_author_display()}: {self.text[:40]}"
