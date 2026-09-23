from decimal import Decimal

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

    global_sale_is_active = models.BooleanField(
        _("Глобальна акція увімкнена"),
        default=False,
        help_text=_(
            "Знижка % на весь асортимент для гостей і звичайних клієнтів. "
            "Перебиває персональну знижку % на варіанті. Косметологи не підпадають."
        ),
    )
    global_sale_percent = models.DecimalField(
        _("Глобальна знижка, %"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(99)],
        help_text=_("Наприклад 20 = мінус 20% від роздрібної. 0 — без знижки."),
    )
    global_sale_starts_at = models.DateTimeField(
        _("Початок глобальної акції"),
        null=True,
        blank=True,
        help_text=_("Порожньо — без обмеження з початку."),
    )
    global_sale_ends_at = models.DateTimeField(
        _("Кінець глобальної акції"),
        null=True,
        blank=True,
        help_text=_("Порожньо — без обмеження з кінця."),
    )
    global_sale_exclude_brands = models.ManyToManyField(
        "catalog.Brand",
        blank=True,
        related_name="+",
        verbose_name=_("Виключити бренди"),
        help_text=_("На ці бренди глобальна акція не діє (лишається персональна sale / роздріб)."),
    )
    global_sale_exclude_products = models.ManyToManyField(
        "catalog.Product",
        blank=True,
        related_name="+",
        verbose_name=_("Виключити товари"),
        help_text=_("На ці товари глобальна акція не діє."),
    )

    class Meta:
        verbose_name = _("Налаштування цін")
        verbose_name_plural = _("Налаштування цін")

    def __str__(self):
        return "Ціни та умови"

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()
        if (
            self.global_sale_starts_at
            and self.global_sale_ends_at
            and self.global_sale_ends_at < self.global_sale_starts_at
        ):
            raise ValidationError(
                {"global_sale_ends_at": _("Кінець акції не може бути раніше за початок.")}
            )
        if self.global_sale_is_active and Decimal(self.global_sale_percent or 0) <= 0:
            raise ValidationError(
                {"global_sale_percent": _("Для увімкненої акції вкажіть відсоток більше 0.")}
            )
