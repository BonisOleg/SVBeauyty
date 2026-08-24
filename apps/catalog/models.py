from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import PublishedModel, SeoModel, TimeStampedModel
from apps.core.utils import localized


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
    image = models.ImageField(_("Фото категорії"), upload_to="categories/", blank=True)
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
    ingredients_uk = models.TextField(_("Склад (укр)"), blank=True)
    ingredients_ru = models.TextField(_("Склад (рос)"), blank=True)
    is_hit = models.BooleanField(_("Хіт продажу"), default=False, db_index=True)
    is_new = models.BooleanField(_("Новинка"), default=False, db_index=True)

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
    def ingredients(self):
        return localized(self, "ingredients")

    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"slug": self.slug})

    @property
    def active_variants(self):
        return [v for v in self.variants.all() if v.is_active]

    @property
    def default_variant(self):
        variants = self.active_variants
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
    image = models.ImageField(_("Зображення"), upload_to="products/")
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
