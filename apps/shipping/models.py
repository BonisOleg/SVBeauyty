from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import SingletonModel, TimeStampedModel


class ShippingSettings(SingletonModel, TimeStampedModel):
    np_api_key = models.CharField(
        _("API-ключ Нової Пошти"),
        max_length=255,
        blank=True,
        help_text=_("Без ключа працює тестовий довідник міст і відділень."),
    )
    use_test_data = models.BooleanField(_("Примусово тестові дані"), default=False)

    pickup_enabled = models.BooleanField(_("Самовивіз увімкнено"), default=True)
    pickup_address_uk = models.CharField(
        _("Адреса самовивозу (укр)"),
        max_length=255,
        blank=True,
        default="м. Київ, вул. Хрещатик, 1",
    )
    pickup_address_ru = models.CharField(
        _("Адреса самовивозу (рос)"),
        max_length=255,
        blank=True,
        default="г. Киев, ул. Крещатик, 1",
    )
    pickup_note_uk = models.CharField(
        _("Підказка самовивозу (укр)"),
        max_length=255,
        blank=True,
        default="Заберіть замовлення після підтвердження менеджером.",
    )
    pickup_note_ru = models.CharField(
        _("Підказка самовивозу (рос)"),
        max_length=255,
        blank=True,
        default="Заберите заказ после подтверждения менеджером.",
    )

    taxi_enabled = models.BooleanField(_("Таксі увімкнено"), default=True)
    taxi_note_uk = models.CharField(
        _("Підказка таксі (укр)"),
        max_length=255,
        blank=True,
        default="Вартість таксі узгоджує менеджер. Вкажіть адресу доставки.",
    )
    taxi_note_ru = models.CharField(
        _("Підказка таксі (рос)"),
        max_length=255,
        blank=True,
        default="Стоимость такси согласует менеджер. Укажите адрес доставки.",
    )

    class Meta:
        verbose_name = _("Налаштування доставки")
        verbose_name_plural = _("Налаштування доставки")

    def __str__(self):
        return "Налаштування доставки"

    @property
    def pickup_address(self):
        from apps.core.utils import localized

        return localized(self, "pickup_address")

    @property
    def pickup_note(self):
        from apps.core.utils import localized

        return localized(self, "pickup_note")

    @property
    def taxi_note(self):
        from apps.core.utils import localized

        return localized(self, "taxi_note")
