from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.storage import document_upload_to, private_document_storage
from apps.accounts.validators import validate_cosmetologist_document
from apps.core.models import TimeStampedModel


class ClientType(models.TextChoices):
    REGULAR = "regular", _("Звичайний клієнт")
    PENDING = "pending_cosmo", _("Заявка косметолога")
    COSMETOLOGIST = "cosmetologist", _("Косметолог")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email обов'язковий")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    username = None
    email = models.EmailField(_("Email"), unique=True)
    phone = models.CharField(_("Телефон"), max_length=32, blank=True, db_index=True)
    client_type = models.CharField(
        _("Тип клієнта"),
        max_length=16,
        choices=ClientType.choices,
        default=ClientType.REGULAR,
        db_index=True,
        help_text=_("Змінюється лише адміністратором."),
    )
    client_type_changed_at = models.DateTimeField(_("Статус змінено"), null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("Клієнт")
        verbose_name_plural = _("Клієнти")

    def __str__(self):
        return self.email

    @property
    def is_pro(self) -> bool:
        return self.client_type == ClientType.COSMETOLOGIST

    @property
    def display_name(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.email


class RequestStatus(models.TextChoices):
    NEW = "new", _("Нова")
    APPROVED = "approved", _("Схвалена")
    REJECTED = "rejected", _("Відхилена")


class CosmetologistRequest(TimeStampedModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cosmetologist_requests", verbose_name=_("Клієнт")
    )
    full_name = models.CharField(_("ПІБ"), max_length=160)
    phone = models.CharField(_("Телефон"), max_length=32)
    workplace = models.CharField(_("Місце роботи"), max_length=255, blank=True)
    document = models.FileField(
        _("Документ"),
        upload_to=document_upload_to,
        storage=private_document_storage,
        blank=True,
        validators=[validate_cosmetologist_document],
        help_text=_("PDF або зображення до 5 МБ. Файл не публічний."),
    )
    comment = models.TextField(_("Коментар"), blank=True)
    status = models.CharField(
        _("Статус"), max_length=16, choices=RequestStatus.choices, default=RequestStatus.NEW, db_index=True
    )
    admin_note = models.TextField(_("Нотатка менеджера"), blank=True)

    class Meta:
        verbose_name = _("Заявка косметолога")
        verbose_name_plural = _("Заявки косметологів")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.get_status_display()}"
