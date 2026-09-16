from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import PublishedModel, SeoModel, TimeStampedModel
from apps.core.utils import localized
from apps.core.utils.images import validate_image



class Brand(TimeStampedModel, PublishedModel):
    name = models.CharField(_("Назва"), max_length=120, unique=True)
    slug = models.SlugField(_("URL"), max_length=140, unique=True)
    description_uk = models.TextField(_("Опис (укр)"), blank=True)
    description_ru = models.TextField(_("Опис (рос)"), blank=True)

    class Meta:
        verbose_name = _("Бренд")
        verbose_name_plural = _("Бренди")
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Category(TimeStampedModel, PublishedModel, SeoModel):
    name_uk = models.CharField(_("Назва (укр)"), max_length=120)
    name_ru = models.CharField(_("Назва (рос)"), max_length=120, blank=True)
    slug = models.SlugField(_("URL"), max_length=140, unique=True)
    image = models.ImageField(
        _("Фото категорії"),
        upload_to="categories/",
        blank=True,
        validators=[validate_image],
    )

    description_uk = models.TextField(_("Опис (укр)"), blank=True)
    description_ru = models.TextField(_("Опис (рос)"), blank=True)

    class Meta:
        verbose_name = _("Категорія")
        verbose_name_plural = _("Категорії")
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name_uk

    @property
    def name(self):
        return localized(self, "name")

    @property
    def description(self):
        return localized(self, "description")

    def get_absolute_url(self):
        return reverse("catalog:category", kwargs={"slug": self.slug})


class Product(TimeStampedModel, PublishedModel, SeoModel):
    brand = models.ForeignKey(
        Brand, on_delete=models.PROTECT, related_name="products", verbose_name=_("Бренд")
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products", verbose_name=_("Категорія")
    )
    name_uk = models.CharField(_("Назва (укр)"), max_length=255)
    name_ru = models.CharField(_("Назва (рос)"), max_length=255, blank=True)
    slug = models.SlugField(_("URL"), max_length=280, unique=True)
    short_description_uk = models.CharField(_("Короткий опис (укр)"), max_length=300, blank=True)
    short_description_ru = models.CharField(_("Короткий опис (рос)"), max_length=300, blank=True)
    description_uk = models.TextField(_("Опис (укр)"), blank=True)
    description_ru = models.TextField(_("Опис (рос)"), blank=True)
    composition_uk = models.TextField(
        _("Склад (укр)"),
        blank=True,
        help_text=_("Текст складу на сторінці товару (вкладка «Склад»)."),
    )
    composition_ru = models.TextField(_("Склад (рос)"), blank=True)
    usage_uk = models.TextField(
        _("Спосіб застосування (укр)"),
        blank=True,
        help_text=_("Текст застосування на сторінці товару (вкладка «Спосіб застосування»)."),
    )
    usage_ru = models.TextField(_("Спосіб застосування (рос)"), blank=True)

    gift_promo_title_uk = models.CharField(
        _("Банер подарунка — заголовок (укр)"),
        max_length=120,
        blank=True,
        default="Пробник у подарунок",
    )
    gift_promo_title_ru = models.CharField(
        _("Банер подарунка — заголовок (рос)"),
        max_length=120,
        blank=True,
        default="Пробник в подарок",
    )
    gift_promo_text_uk = models.TextField(
        _("Банер подарунка — текст (укр)"),
        blank=True,
        help_text=_("Короткий текст на банері. Порожньо — банер не показується."),
    )
    gift_promo_text_ru = models.TextField(_("Банер подарунка — текст (рос)"), blank=True)
    gift_promo_tooltip_uk = models.TextField(
        _("Банер подарунка — підказка «i» (укр)"),
        blank=True,
        help_text=_("Детальний опис акції у спливаючій підказці біля іконки «i»."),
    )
    gift_promo_tooltip_ru = models.TextField(_("Банер подарунка — підказка «i» (рос)"), blank=True)

    is_hit = models.BooleanField(_("Хіт продажу"), default=False, db_index=True)
    is_new = models.BooleanField(_("Новинка"), default=False, db_index=True)
    filter_attrs = models.ManyToManyField(
        "ProductAttribute",
        blank=True,
        related_name="products",
        verbose_name=_("Характеристики для фільтрів"),
        help_text=_("Вік, тип/стан шкіри, інгредієнти — з’являються у фільтрах каталогу."),
    )

    class Meta:
        verbose_name = _("Товар")
        verbose_name_plural = _("Товари")
        ordering = ["sort_order", "-created_at"]
        indexes = [models.Index(fields=["is_active", "category"])]

    def __str__(self):
        return self.name_uk

    @property
    def name(self):
        return localized(self, "name")

    @property
    def short_description(self):
        return localized(self, "short_description")

    @property
    def description(self):
        return localized(self, "description")

    @property
    def composition(self):
        return localized(self, "composition")

    @property
    def usage(self):
        return localized(self, "usage")

    @property
    def gift_promo_title(self):
        return localized(self, "gift_promo_title") or _("Пробник у подарунок")

    @property
    def gift_promo_text(self):
        return localized(self, "gift_promo_text")

    @property
    def gift_promo_tooltip(self):
        return localized(self, "gift_promo_tooltip")

    @property
    def has_gift_promo(self) -> bool:
        return bool((self.gift_promo_text_uk or self.gift_promo_text_ru or "").strip())

    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"slug": self.slug})

    @property
    def active_variants(self):
        return [v for v in self.variants.all() if v.is_active]

    @property
    def default_variant(self):
        variants = self.active_variants
        for variant in variants:
            if variant.in_stock:
                return variant
        return variants[0] if variants else None

    @property
    def main_image(self):
        images = list(self.images.all())
        for image in images:
            if image.is_main:
                return image
        return images[0] if images else None

    @property
    def in_stock(self) -> bool:
        return any(v.in_stock for v in self.active_variants)

    @property
    def rating_avg(self) -> float:
        cached = getattr(self, "_rating_avg", None)
        if cached is not None:
            return float(cached or 0)
        value = self.reviews.filter(is_published=True).aggregate(avg=Avg("rating"))["avg"]
        return float(value or 0)

    @property
    def rating_count(self) -> int:
        cached = getattr(self, "_rating_count", None)
        if cached is not None:
            return int(cached or 0)
        return self.reviews.filter(is_published=True).count()

    @property
    def rating_stars(self) -> int:
        """Округлені зірки 0–5 для відображення."""
        return int(round(self.rating_avg))


class Variant(TimeStampedModel, PublishedModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants", verbose_name=_("Товар")
    )
    sku = models.CharField(_("Артикул"), max_length=64, unique=True)
    volume = models.CharField(_("Об'єм"), max_length=32)

    purchase_price_uah = models.DecimalField(
        _("Закупівельна ціна, грн"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Службове поле, на сайті не показується. Від нього рахуються інші ціни."),
    )
    price_uah = models.DecimalField(
        _("Роздрібна ціна, грн"),
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True,
        help_text=_("Порожньо — порахується автоматично від закупівельної плюс націнка."),
    )
    price_is_manual = models.BooleanField(
        _("Роздрібна ціна вручну"),
        default=False,
        help_text=_("Увімкніть, щоб автоперерахунок не перезаписував цю ціну."),
    )
    price_pro_uah = models.DecimalField(
        _("Ціна для косметологів, грн"),
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True,
        help_text=_("Порожньо — порахується автоматично від закупівельної плюс націнка."),
    )
    price_pro_is_manual = models.BooleanField(
        _("Ціна косметолога вручну"),
        default=False,
        help_text=_("Увімкніть, щоб автоперерахунок не перезаписував цю ціну."),
    )

    sale_price_uah = models.DecimalField(
        _("Акційна ціна, грн"),
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True,
        help_text=_(
            "Для гостей і звичайних клієнтів. Показується, якщо більша за 0 і менша за роздрібну. "
            "Косметологи бачать pro-ціну без акції. 0 — без акції."
        ),
    )

    stock_qty = models.PositiveIntegerField(_("Залишок"), default=0)

    class Meta:
        verbose_name = _("Варіант (об'єм)")
        verbose_name_plural = _("Варіанти (об'єми)")
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.product.name_uk} — {self.volume}"

    def save(self, *args, **kwargs):
        from apps.pricing.services import apply_auto_prices

        apply_auto_prices(self)
        super().save(*args, **kwargs)

    @property
    def in_stock(self) -> bool:
        return self.stock_qty > 0

    @property
    def margin_uah(self):
        return self.price_uah - self.purchase_price_uah

    @property
    def margin_pro_uah(self):
        return self.price_pro_uah - self.purchase_price_uah


class ProductImage(TimeStampedModel, PublishedModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images", verbose_name=_("Товар")
    )
    image = models.ImageField(
        _("Зображення"),
        upload_to="products/",
        validators=[validate_image],
    )

    alt_uk = models.CharField(_("Alt (укр)"), max_length=255, blank=True)
    alt_ru = models.CharField(_("Alt (рос)"), max_length=255, blank=True)
    is_main = models.BooleanField(_("Головне фото"), default=False)

    class Meta:
        verbose_name = _("Фото товару")
        verbose_name_plural = _("Фото товарів")
        ordering = ["-is_main", "sort_order", "id"]

    def __str__(self):
        return f"{self.product.name_uk} — фото {self.pk}"

    @property
    def alt(self):
        return localized(self, "alt") or self.product.name


class ProductAttributeGroup(TimeStampedModel, PublishedModel):
    """Група характеристик для фільтрів (вік, тип шкіри тощо)."""

    class Slug(models.TextChoices):
        AGE = "age", _("За віком")
        SKIN_TYPE = "skin_type", _("За типом шкіри")
        SKIN_CONDITION = "skin_condition", _("За станом шкіри")
        INGREDIENT = "ingredient", _("Інгредієнти")

    slug = models.SlugField(_("Код"), max_length=40, unique=True, choices=Slug.choices)
    name_uk = models.CharField(_("Назва (укр)"), max_length=120)
    name_ru = models.CharField(_("Назва (рос)"), max_length=120, blank=True)

    class Meta:
        verbose_name = _("Група характеристик")
        verbose_name_plural = _("Групи характеристик")
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name_uk

    @property
    def name(self):
        return localized(self, "name")


class ProductAttribute(TimeStampedModel, PublishedModel):
    """Значення характеристики (напр. «35+», «суха», «ніацинамід»)."""

    group = models.ForeignKey(
        ProductAttributeGroup,
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name=_("Група"),
    )
    name_uk = models.CharField(_("Назва (укр)"), max_length=120)
    name_ru = models.CharField(_("Назва (рос)"), max_length=120, blank=True)
    slug = models.SlugField(_("URL"), max_length=140)

    class Meta:
        verbose_name = _("Характеристика")
        verbose_name_plural = _("Характеристики")
        ordering = ["group__sort_order", "sort_order", "name_uk"]
        constraints = [
            models.UniqueConstraint(fields=["group", "slug"], name="uniq_attr_group_slug"),
        ]

    def __str__(self):
        return f"{self.group.name_uk}: {self.name_uk}"

    @property
    def name(self):
        return localized(self, "name")


class WishlistItem(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name=_("Клієнт"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
        verbose_name=_("Товар"),
    )

    class Meta:
        verbose_name = _("Обране")
        verbose_name_plural = _("Обране")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="uniq_wishlist_user_product"),
        ]

    def __str__(self):
        return f"{self.user_id} → {self.product_id}"


class ProductReview(TimeStampedModel):
    """Відгук покупця: зірки + текст для картки та PDP (як на Makeup)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Товар"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_reviews",
        verbose_name=_("Користувач"),
    )
    author_name = models.CharField(_("Імʼя автора"), max_length=120)
    rating = models.PositiveSmallIntegerField(
        _("Оцінка"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField(_("Текст відгуку"), blank=True)
    is_verified_purchase = models.BooleanField(
        _("Покупка підтверджена"),
        default=False,
        help_text=_("Ставиться лише якщо користувач має оплачене замовлення з цим товаром."),
    )
    is_published = models.BooleanField(
        _("Опубліковано"),
        default=False,
        db_index=True,
        help_text=_("Нові відгуки чекають модерації в адмінці."),
    )

    class Meta:
        verbose_name = _("Відгук")
        verbose_name_plural = _("Відгуки")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product_id}: {self.rating}★ — {self.author_name}"
