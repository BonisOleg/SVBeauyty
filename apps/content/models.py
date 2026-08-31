from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import PublishedModel, SeoModel, SingletonModel, TimeStampedModel
from apps.core.utils import localize_path, localized

HEX_COLOR = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message=_("Вкажіть колір у форматі #RRGGBB."),
)


class SiteSettings(SingletonModel, TimeStampedModel):
    site_name = models.CharField(_("Назва сайту"), max_length=120, default="SVbeauty")
    logo = models.ImageField(_("Логотип"), upload_to="brand/", blank=True)
    accent_color = models.CharField(_("Акцентний колір (HEX)"), max_length=7, default="#1A1A1A")

    phone = models.CharField(_("Телефон"), max_length=32, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    manager_email = models.EmailField(_("Email менеджера (чат, замовлення)"), blank=True)
    viber = models.CharField(_("Viber"), max_length=255, blank=True, help_text=_("URL або номер телефону"))
    telegram = models.CharField(_("Telegram"), max_length=255, blank=True, help_text=_("URL, напр. https://t.me/..."))
    whatsapp = models.CharField(_("WhatsApp"), max_length=255, blank=True, help_text=_("URL або номер телефону"))
    instagram = models.CharField(_("Instagram"), max_length=255, blank=True, help_text=_("URL профілю"))
    tiktok = models.CharField(_("TikTok"), max_length=255, blank=True, help_text=_("URL профілю"))
    work_hours_uk = models.CharField(_("Графік роботи (укр)"), max_length=120, blank=True)
    work_hours_ru = models.CharField(_("Графік роботи (рос)"), max_length=120, blank=True)

    promo_is_active = models.BooleanField(_("Показувати промо-смугу"), default=False)
    promo_text_uk = models.CharField(_("Промо-текст (укр)"), max_length=255, blank=True)
    promo_text_ru = models.CharField(_("Промо-текст (рос)"), max_length=255, blank=True)

    slogan_uk = models.CharField(
        _("Слоган у футері (укр)"),
        max_length=255,
        blank=True,
        default="Професійна косметика для домашнього та салонного догляду.",
    )
    slogan_ru = models.CharField(
        _("Слоган у футері (рос)"),
        max_length=255,
        blank=True,
        default="Профессиональная косметика для домашнего и салонного ухода.",
    )
    meta_description_uk = models.CharField(
        _("Meta / OG опис (укр)"),
        max_length=300,
        blank=True,
        default="Професійна косметика для домашнього та салонного догляду.",
    )
    meta_description_ru = models.CharField(
        _("Meta / OG опис (рос)"),
        max_length=300,
        blank=True,
        default="Профессиональная косметика для домашнего и салонного ухода.",
    )

    hero_title_uk = models.CharField(
        _("Hero без банерів — заголовок (укр)"),
        max_length=255,
        blank=True,
        default="Професійний догляд за шкірою",
    )
    hero_title_ru = models.CharField(
        _("Hero без банерів — заголовок (рос)"),
        max_length=255,
        blank=True,
        default="Профессиональный уход за кожей",
    )
    hero_subtitle_uk = models.CharField(
        _("Hero без банерів — підзаголовок (укр)"),
        max_length=300,
        blank=True,
        default="Пілінги, сироватки, креми та SPF для домашнього і салонного застосування.",
    )
    hero_subtitle_ru = models.CharField(
        _("Hero без банерів — підзаголовок (рос)"),
        max_length=300,
        blank=True,
        default="Пилинги, сыворотки, кремы и SPF для домашнего и салонного применения.",
    )
    hero_button_uk = models.CharField(
        _("Hero без банерів — кнопка (укр)"),
        max_length=60,
        blank=True,
        default="До каталогу",
    )
    hero_button_ru = models.CharField(
        _("Hero без банерів — кнопка (рос)"),
        max_length=60,
        blank=True,
        default="В каталог",
    )

    pro_cta_title_uk = models.CharField(
        _("Блок косметологам — заголовок (укр)"),
        max_length=120,
        blank=True,
        default="Ви косметолог?",
    )
    pro_cta_title_ru = models.CharField(
        _("Блок косметологам — заголовок (рос)"),
        max_length=120,
        blank=True,
        default="Вы косметолог?",
    )
    pro_cta_text_uk = models.CharField(
        _("Блок косметологам — текст (укр)"),
        max_length=400,
        blank=True,
        default=(
            "Отримайте професійні ціни та окремі умови доставки. "
            "Надішліть заявку — менеджер підтвердить статус."
        ),
    )
    pro_cta_text_ru = models.CharField(
        _("Блок косметологам — текст (рос)"),
        max_length=400,
        blank=True,
        default=(
            "Получите профессиональные цены и отдельные условия доставки. "
            "Отправьте заявку — менеджер подтвердит статус."
        ),
    )
    pro_cta_button_uk = models.CharField(
        _("Блок косметологам — кнопка (укр)"),
        max_length=60,
        blank=True,
        default="Подати заявку",
    )
    pro_cta_button_ru = models.CharField(
        _("Блок косметологам — кнопка (рос)"),
        max_length=60,
        blank=True,
        default="Подать заявку",
    )
    pro_cta_image = models.ImageField(
        _("Блок косметологам — зображення"),
        upload_to="brand/",
        blank=True,
        help_text=_("Фон на весь блок. Рекомендовано 1600×560, JPG/WebP."),
    )
    pro_cta_image_mobile = models.ImageField(
        _("Блок косметологам — зображення (мобільне)"),
        upload_to="brand/",
        blank=True,
        help_text=_("Опційно. Якщо порожньо — показується десктопне. Рекомендовано 900×700."),
    )
    pro_cta_bg_color = models.CharField(
        _("Блок косметологам — колір фону"),
        max_length=7,
        default="#1A1A1A",
        validators=[HEX_COLOR],
        help_text=_("Видно без фото або під градієнтом поверх фото. #RRGGBB."),
    )
    pro_cta_text_color = models.CharField(
        _("Блок косметологам — колір тексту"),
        max_length=7,
        default="#FFFFFF",
        validators=[HEX_COLOR],
    )
    pro_cta_button_color = models.CharField(
        _("Блок косметологам — колір кнопки"),
        max_length=7,
        default="#FFFFFF",
        validators=[HEX_COLOR],
    )
    pro_cta_button_text_color = models.CharField(
        _("Блок косметологам — колір тексту кнопки"),
        max_length=7,
        default="#111111",
        validators=[HEX_COLOR],
    )

    usp1_title_uk = models.CharField(
        _("USP 1 — заголовок (укр)"), max_length=120, blank=True, default="Оригінальна продукція"
    )
    usp1_title_ru = models.CharField(
        _("USP 1 — заголовок (рос)"), max_length=120, blank=True, default="Оригинальная продукция"
    )
    usp1_text_uk = models.CharField(
        _("USP 1 — текст (укр)"), max_length=255, blank=True, default="Працюємо напряму з виробником."
    )
    usp1_text_ru = models.CharField(
        _("USP 1 — текст (рос)"),
        max_length=255,
        blank=True,
        default="Работаем напрямую с производителем.",
    )
    usp2_title_uk = models.CharField(
        _("USP 2 — заголовок (укр)"), max_length=120, blank=True, default="Доставка Новою Поштою"
    )
    usp2_title_ru = models.CharField(
        _("USP 2 — заголовок (рос)"), max_length=120, blank=True, default="Доставка Новой Почтой"
    )
    usp2_text_uk = models.CharField(
        _("USP 2 — текст (укр)"),
        max_length=255,
        blank=True,
        default="Відділення та поштомати по всій Україні.",
    )
    usp2_text_ru = models.CharField(
        _("USP 2 — текст (рос)"),
        max_length=255,
        blank=True,
        default="Отделения и почтоматы по всей Украине.",
    )
    usp3_title_uk = models.CharField(
        _("USP 3 — заголовок (укр)"), max_length=120, blank=True, default="Бонусна програма"
    )
    usp3_title_ru = models.CharField(
        _("USP 3 — заголовок (рос)"), max_length=120, blank=True, default="Бонусная программа"
    )
    usp3_text_uk = models.CharField(
        _("USP 3 — текст (укр)"),
        max_length=255,
        blank=True,
        default="Накопичуйте бали та оплачуйте ними покупки.",
    )
    usp3_text_ru = models.CharField(
        _("USP 3 — текст (рос)"),
        max_length=255,
        blank=True,
        default="Накапливайте баллы и оплачивайте ими покупки.",
    )
    usp4_title_uk = models.CharField(
        _("USP 4 — заголовок (укр)"), max_length=120, blank=True, default="Консультація"
    )
    usp4_title_ru = models.CharField(
        _("USP 4 — заголовок (рос)"), max_length=120, blank=True, default="Консультация"
    )
    usp4_text_uk = models.CharField(
        _("USP 4 — текст (укр)"),
        max_length=255,
        blank=True,
        default="Допоможемо підібрати догляд у чаті.",
    )
    usp4_text_ru = models.CharField(
        _("USP 4 — текст (рос)"),
        max_length=255,
        blank=True,
        default="Поможем подобрать уход в чате.",
    )

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
    def slogan(self):
        return localized(self, "slogan")

    @property
    def meta_description(self):
        return localized(self, "meta_description")

    @property
    def hero_title(self):
        return localized(self, "hero_title")

    @property
    def hero_subtitle(self):
        return localized(self, "hero_subtitle")

    @property
    def hero_button(self):
        return localized(self, "hero_button")

    @property
    def pro_cta_title(self):
        return localized(self, "pro_cta_title")

    @property
    def pro_cta_text(self):
        return localized(self, "pro_cta_text")

    @property
    def pro_cta_button(self):
        return localized(self, "pro_cta_button")

    def usp_items(self) -> list[dict[str, str]]:
        items = []
        for index in range(1, 5):
            title = localized(self, f"usp{index}_title")
            text = localized(self, f"usp{index}_text")
            if title or text:
                items.append({"title": title, "text": text})
        return items

    @property
    def phone_href(self) -> str:
        return "".join(ch for ch in self.phone if ch.isdigit() or ch == "+")

    @staticmethod
    def _messenger_href(value: str, *, phone_scheme: str = "") -> str:
        raw = (value or "").strip()
        if not raw:
            return ""
        lower = raw.lower()
        if lower.startswith(("http://", "https://", "viber://", "tg://", "whatsapp://", "mailto:")):
            return raw
        if phone_scheme:
            digits = "".join(ch for ch in raw if ch.isdigit())
            if digits:
                return f"{phone_scheme}{digits}"
        return raw

    @property
    def social_links(self) -> list[dict[str, str]]:
        """Посилання для футера: лише заповнені поля з адмінки."""
        items = [
            ("instagram", "Instagram", self._messenger_href(self.instagram)),
            ("telegram", "Telegram", self._messenger_href(self.telegram)),
            ("viber", "Viber", self._messenger_href(self.viber, phone_scheme="viber://chat?number=")),
            ("whatsapp", "WhatsApp", self._messenger_href(self.whatsapp, phone_scheme="https://wa.me/")),
            ("tiktok", "TikTok", self._messenger_href(self.tiktok)),
        ]
        return [{"key": key, "label": label, "href": href} for key, label, href in items if href]

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
    text_color = models.CharField(
        _("Колір тексту"),
        max_length=7,
        default="#FFFFFF",
        validators=[HEX_COLOR],
        help_text=_("Заголовок і підзаголовок. Формат #RRGGBB."),
    )
    button_color = models.CharField(
        _("Колір кнопки"),
        max_length=7,
        default="#111111",
        validators=[HEX_COLOR],
        help_text=_("Фон кнопки. Формат #RRGGBB."),
    )
    button_text_color = models.CharField(
        _("Колір тексту кнопки"),
        max_length=7,
        default="#FFFFFF",
        validators=[HEX_COLOR],
        help_text=_("Текст на кнопці. Формат #RRGGBB."),
    )
    button_text_uk = models.CharField(_("Кнопка (укр)"), max_length=60, blank=True)
    button_text_ru = models.CharField(_("Кнопка (рос)"), max_length=60, blank=True)
    button_url = models.CharField(
        _("Посилання кнопки"),
        max_length=255,
        blank=True,
        help_text=_(
            "Шлях без мови, напр. /catalog/syrovatky/. "
            "Префікс /uk/ або /ru/ підставиться автоматично. "
            "Зовнішні посилання (https://...) — без змін."
        ),
    )

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

    @property
    def button_href(self) -> str:
        return localize_path(self.button_url)
