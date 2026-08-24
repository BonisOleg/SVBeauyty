from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import SingletonModel, TimeStampedModel


class RoundingStep(models.TextChoices):
    CENT = "0.01", _("До копійки")
    UAH = "1.00", _("До гривні")
    FIVE = "5.00", _("До 5 грн")
    TEN = "10.00", _("До 10 грн")


class PricingSettings(SingletonModel, TimeStampedModel):
    retail_markup_percent = models.DecimalField(
        _("Націнка роздріб, %"),
        max_digits=6,
        decimal_places=2,
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text=_("Роздрібна ціна = закупівельна + ця націнка."),
    )
    pro_markup_percent = models.DecimalField(
        _("Націнка для косметологів, %"),
        max_digits=6,
        decimal_places=2,
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text=_("Ціна для косметологів = закупівельна + ця націнка."),
    )
    rounding_step = models.CharField(
        _("Округлення цін"),
        max_length=8,
        choices=RoundingStep.choices,
        default=RoundingStep.UAH,
    )
    pro_min_order_uah = models.DecimalField(
        _("Мінімальне замовлення для косметологів, грн"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    pro_delivery_note_uk = models.TextField(_("Умови доставки для косметологів (укр)"), blank=True)
    pro_delivery_note_ru = models.TextField(_("Умови доставки для косметологів (рос)"), blank=True)
    retail_delivery_note_uk = models.TextField(_("Умови доставки роздріб (укр)"), blank=True)
    retail_delivery_note_ru = models.TextField(_("Умови доставки роздріб (рос)"), blank=True)
    free_delivery_from_uah = models.DecimalField(
        _("Безкоштовна доставка від, грн"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    free_delivery_from_pro_uah = models.DecimalField(
        _("Безкоштовна доставка для косметологів від, грн"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Ціни та умови")
        verbose_name_plural = _("Ціни та умови")

    def __str__(self):
        return "Ціни та умови"
