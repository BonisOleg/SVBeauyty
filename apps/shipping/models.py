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

    class Meta:
        verbose_name = _("Доставка")
        verbose_name_plural = _("Доставка")

    def __str__(self):
        return "Налаштування доставки"
