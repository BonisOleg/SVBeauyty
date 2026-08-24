from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import SingletonModel, TimeStampedModel


class LoyaltySettings(SingletonModel, TimeStampedModel):
    is_enabled = models.BooleanField(_("Програма увімкнена"), default=True)
    earn_points_per_uah = models.DecimalField(
        _("Балів за 1 грн"),
        max_digits=6,
        decimal_places=4,
        default=Decimal("0.0500"),
        help_text=_("0.05 = 5 балів за кожні 100 грн."),
    )
    redeem_uah_per_point = models.DecimalField(
        _("Грн за 1 бал"), max_digits=6, decimal_places=2, default=Decimal("1.00")
    )
    max_redeem_percent = models.DecimalField(
        _("Максимум списання, % від суми"),
        max_digits=5,
        decimal_places=2,
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    earn_for_pro = models.BooleanField(_("Нараховувати косметологам"), default=False)

    class Meta:
        verbose_name = _("Програма лояльності")
        verbose_name_plural = _("Програма лояльності")

    def __str__(self):
        return "Програма лояльності"


class LoyaltyAccount(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loyalty_account",
        verbose_name=_("Клієнт"),
    )
    balance = models.IntegerField(_("Баланс балів"), default=0)

    class Meta:
        verbose_name = _("Бонусний рахунок")
        verbose_name_plural = _("Бонусні рахунки")

    def __str__(self):
        return f"{self.user.email}: {self.balance}"


class TransactionKind(models.TextChoices):
    EARN = "earn", _("Нарахування")
    REDEEM = "redeem", _("Списання")
    MANUAL = "manual", _("Ручна операція")


class LoyaltyTransaction(TimeStampedModel):
    account = models.ForeignKey(
        LoyaltyAccount, on_delete=models.CASCADE, related_name="transactions", verbose_name=_("Рахунок")
    )
    order = models.ForeignKey(
        "commerce.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loyalty_transactions",
        verbose_name=_("Замовлення"),
    )
    kind = models.CharField(_("Тип"), max_length=16, choices=TransactionKind.choices)
    points = models.IntegerField(_("Бали"), help_text=_("Плюс — нарахування, мінус — списання."))
    balance_after = models.IntegerField(_("Баланс після"), default=0)
    comment = models.CharField(_("Коментар"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Бонусна операція")
        verbose_name_plural = _("Бонусні операції")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "kind"],
                condition=models.Q(order__isnull=False),
                name="loyalty_unique_order_kind",
            )
        ]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.points}"
