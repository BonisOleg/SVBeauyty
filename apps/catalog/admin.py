from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from apps.catalog.forms import VariantAdminForm
from apps.catalog.models import Brand, Category, Product, ProductImage, Variant
from apps.pricing import services as pricing_services


class VariantInline(TabularInline):
    model = Variant
    form = VariantAdminForm
    extra = 1
    fields = [
        "sku",
        "volume",
        "purchase_price_uah",
        "price_uah",
        "price_is_manual",
        "price_pro_uah",
        "price_pro_is_manual",
        "stock_qty",
        "is_active",
        "sort_order",
    ]


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "alt_uk", "alt_ru", "is_main", "sort_order"]


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ["name", "slug", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name_uk", "name_ru", "slug", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    prepopulated_fields = {"slug": ("name_uk",)}
    search_fields = ["name_uk", "name_ru"]
    fieldsets = [
        (None, {"fields": ["name_uk", "name_ru", "slug", "image", "is_active", "sort_order"]}),
        ("Описи", {"fields": ["description_uk", "description_ru"], "classes": ["collapse"]}),
        (
            "SEO",
            {
                "fields": ["seo_title_uk", "seo_title_ru", "seo_description_uk", "seo_description_ru"],
                "classes": ["collapse"],
            },
        ),
    ]


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ["preview", "name_uk", "brand", "category", "price_summary", "is_active", "is_hit", "is_new"]
    list_display_links = ["preview", "name_uk"]
    list_editable = ["is_active", "is_hit", "is_new"]
    list_filter = ["category", "brand", "is_active", "is_hit", "is_new"]
    search_fields = ["name_uk", "name_ru", "variants__sku"]
    prepopulated_fields = {"slug": ("name_uk",)}
    inlines = [VariantInline, ProductImageInline]
    list_select_related = ["brand", "category"]
    fieldsets = [
        (None, {"fields": ["brand", "category", "name_uk", "name_ru", "slug"]}),
        ("Позначки", {"fields": ["is_hit", "is_new", "is_active", "sort_order"]}),
        ("Короткий опис", {"fields": ["short_description_uk", "short_description_ru"]}),
        ("Повний опис", {"fields": ["description_uk", "description_ru"], "classes": ["collapse"]}),
        ("Склад", {"fields": ["ingredients_uk", "ingredients_ru"], "classes": ["collapse"]}),
        (
            "SEO",
            {
                "fields": ["seo_title_uk", "seo_title_ru", "seo_description_uk", "seo_description_ru"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Фото")
    def preview(self, obj):
        image = obj.main_image
        if not image:
            return "—"
        return format_html('<img src="{}" style="width:44px;height:44px;object-fit:cover;border-radius:6px">', image.image.url)

    @admin.display(description="Закуп → роздріб / космет., грн")
    def price_summary(self, obj):
        variants = obj.active_variants
        if not variants:
            return "—"
        return ", ".join(
            f"{v.volume}: {v.purchase_price_uah:g} → {v.price_uah:g} / {v.price_pro_uah:g}"
            for v in variants
        )


@admin.register(Variant)
class VariantAdmin(ModelAdmin):
    form = VariantAdminForm
    list_display = [
        "sku",
        "product",
        "volume",
        "purchase_price_uah",
        "price_uah",
        "price_is_manual",
        "price_pro_uah",
        "price_pro_is_manual",
        "stock_qty",
        "is_active",
    ]
    list_editable = [
        "purchase_price_uah",
        "price_uah",
        "price_is_manual",
        "price_pro_uah",
        "price_pro_is_manual",
        "stock_qty",
        "is_active",
    ]
    list_filter = ["is_active", "price_is_manual", "price_pro_is_manual", "product__category"]
    search_fields = ["sku", "product__name_uk"]
    list_select_related = ["product"]
    actions = ["action_recalculate", "action_reset_to_auto"]
    fieldsets = [
        (None, {"fields": ["product", "sku", "volume", "stock_qty", "is_active", "sort_order"]}),
        (
            "Ціни",
            {
                "fields": [
                    "purchase_price_uah",
                    ("price_uah", "price_is_manual"),
                    ("price_pro_uah", "price_pro_is_manual"),
                ],
                "description": (
                    "Введіть закупівельну ціну — роздрібна й ціна для косметологів заповняться "
                    "автоматично за націнками з розділу «Ціни та умови». Щоб задати ціну вручну, "
                    "впишіть її та поставте відповідну галочку."
                ),
            },
        ),
    ]

    @admin.action(description="Перерахувати ціни за націнками")
    def action_recalculate(self, request, queryset):
        count = pricing_services.recalculate_all(queryset)
        self.message_user(request, f"Оновлено цін: {count}.")

    @admin.action(description="Зняти ручний режим і перерахувати")
    def action_reset_to_auto(self, request, queryset):
        queryset.update(price_is_manual=False, price_pro_is_manual=False)
        count = pricing_services.recalculate_all(queryset)
        self.message_user(request, f"Переведено на автоціни: {count}.")
