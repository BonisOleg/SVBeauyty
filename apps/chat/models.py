import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.chat.storage import chat_upload_to, private_chat_storage
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
    text = models.TextField(_("Повідомлення"), blank=True)
    is_read = models.BooleanField(_("Прочитано"), default=False)
    is_deleted = models.BooleanField(_("Видалено"), default=False, db_index=True)
    deleted_at = models.DateTimeField(_("Видалено о"), null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_messages_authored",
        verbose_name=_("Автор (менеджер)"),
        help_text=_("Хто з персоналу надіслав повідомлення. Потрібно, щоб видаляти лише свої."),
    )

    class Meta:
        verbose_name = _("Повідомлення")
        verbose_name_plural = _("Повідомлення")
        ordering = ["created_at"]

    def __str__(self):
        prefix = "[deleted] " if self.is_deleted else ""
        return f"{prefix}{self.get_author_display()}: {self.text[:40]}"

    def soft_delete(self) -> None:
        if self.is_deleted:
            return
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])


class AttachmentKind(models.TextChoices):
    IMAGE = "image", _("Зображення")
    PDF = "pdf", _("PDF")


class ChatAttachment(TimeStampedModel):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Повідомлення"),
    )
    file = models.FileField(
        _("Файл"),
        upload_to=chat_upload_to,
        storage=private_chat_storage,
        max_length=240,
    )
    original_name = models.CharField(_("Назва"), max_length=180)
    kind = models.CharField(_("Тип"), max_length=8, choices=AttachmentKind.choices)
    size = models.PositiveIntegerField(_("Розмір, байти"), default=0)

    class Meta:
        verbose_name = _("Вкладення")
        verbose_name_plural = _("Вкладення")
        ordering = ["created_at"]

    def __str__(self):
        return self.original_name

