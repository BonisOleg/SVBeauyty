from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import PublishedModel, SeoModel, SingletonModel, TimeStampedModel
from apps.core.utils import localized


class SiteSettings(SingletonModel, TimeStampedModel):
    site_name = models.CharField(_("Назва сайту"), max_length=120, default="SVbeauty")
    logo = models.ImageField(_("Логотип"), upload_to="brand/", blank=True)
    accent_color = models.CharField(_("Акцентний колір (HEX)"), max_length=7, default="#20847C")

    phone = models.CharField(_("Телефон"), max_length=32, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    manager_email = models.EmailField(_("Email менеджера (чат, замовлення)"), blank=True)
    viber = models.CharField(_("Viber"), max_length=255, blank=True)
    telegram = models.CharField(_("Telegram"), max_length=255, blank=True)
    whatsapp = models.CharField(_("WhatsApp"), max_length=255, blank=True)
    instagram = models.CharField(_("Instagram"), max_length=255, blank=True)
    work_hours_uk = models.CharField(_("Графік роботи (укр)"), max_length=120, blank=True)
    work_hours_ru = models.CharField(_("Графік роботи (рос)"), max_length=120, blank=True)

    promo_is_active = models.BooleanField(_("Показувати промо-смугу"), default=False)
    promo_text_uk = models.CharField(_("Промо-текст (укр)"), max_length=255, blank=True)
    promo_text_ru = models.CharField(_("Промо-текст (рос)"), max_length=255, blank=True)

    bank_recipient = models.CharField(_("Отримувач"), max_length=255, blank=True)
    bank_tax_id = models.CharField(_("ІПН / ЄДРПОУ"), max_length=32, blank=True)
    bank_iban = models.CharField(_("IBAN"), max_length=64, blank=True)
    bank_name = models.CharField(_("Банк"), max_length=160, blank=True)
    bank_purpose_template = models.CharField(
        _("Призначення платежу"),
        max_length=255,
        blank=True,
        default="Оплата замовлення {order_number}",
        help_text=_("Доступний плейсхолдер {order_number}."),
    )

    class Meta:
        verbose_name = _("Налаштування сайту")
        verbose_name_plural = _("Налаштування сайту")

    def __str__(self):
        return "Налаштування сайту"

    @property
    def promo_text(self):
        return localized(self, "promo_text")

    @property
    def work_hours(self):
        return localized(self, "work_hours")

    @property
    def phone_href(self) -> str:
        return "".join(ch for ch in self.phone if ch.isdigit() or ch == "+")

    def bank_details(self, order_number: str = "") -> dict:
        purpose = (self.bank_purpose_template or "").replace("{order_number}", order_number)
        return {
            "recipient": self.bank_recipient,
            "tax_id": self.bank_tax_id,
            "iban": self.bank_iban,
            "bank": self.bank_name,
            "purpose": purpose,
        }


class Page(TimeStampedModel, PublishedModel, SeoModel):
    slug = models.SlugField(_("URL"), max_length=140, unique=True)
    title_uk = models.CharField(_("Заголовок (укр)"), max_length=255)
    title_ru = models.CharField(_("Заголовок (рос)"), max_length=255, blank=True)
    body_uk = models.TextField(_("Текст (укр)"), blank=True)
    body_ru = models.TextField(_("Текст (рос)"), blank=True)
    body_pro_uk = models.TextField(_("Текст для косметологів (укр)"), blank=True)
    body_pro_ru = models.TextField(_("Текст для косметологів (рос)"), blank=True)

    class Meta:
        verbose_name = _("Сторінка")
        verbose_name_plural = _("Сторінки")
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title_uk

    @property
    def title(self):
        return localized(self, "title")

    @property
    def body(self):
        return localized(self, "body")

    @property
    def body_pro(self):
        return localized(self, "body_pro")

    def get_absolute_url(self):
        return reverse("content:page", kwargs={"slug": self.slug})


class Banner(TimeStampedModel, PublishedModel):
    title_uk = models.CharField(_("Заголовок (укр)"), max_length=255)
    title_ru = models.CharField(_("Заголовок (рос)"), max_length=255, blank=True)
    subtitle_uk = models.CharField(_("Підзаголовок (укр)"), max_length=300, blank=True)
    subtitle_ru = models.CharField(_("Підзаголовок (рос)"), max_length=300, blank=True)
    image = models.ImageField(
        _("Зображення (десктоп)"),
        upload_to="banners/",
        blank=True,
        help_text=_("Співвідношення 21:9. Рекомендовано 1680×720 або 1920×823 px, JPG/WebP."),
    )
    image_mobile = models.ImageField(
        _("Зображення (мобільне)"),
        upload_to="banners/",
        blank=True,
        help_text=_("Співвідношення 3:4. Рекомендовано 900×1200 px, JPG/WebP. Показується до 599 px."),
    )
    button_text_uk = models.CharField(_("Кнопка (укр)"), max_length=60, blank=True)
    button_text_ru = models.CharField(_("Кнопка (рос)"), max_length=60, blank=True)
    button_url = models.CharField(_("Посилання кнопки"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Банер")
        verbose_name_plural = _("Банери")
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title_uk

    @property
    def title(self):
        return localized(self, "title")

    @property
    def subtitle(self):
        return localized(self, "subtitle")

    @property
    def button_text(self):
        return localized(self, "button_text")
