from django import forms
from django.contrib import admin
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from apps.content.models import Banner, Page, SiteSettings


class SingletonAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class HexColorInput(forms.TextInput):
    input_type = "color"


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdmin):
    color_fields = {
        "pro_cta_bg_color",
        "pro_cta_text_color",
        "pro_cta_button_color",
        "pro_cta_button_text_color",
    }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.color_fields:
            kwargs["widget"] = HexColorInput()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    fieldsets = [
        ("Бренд", {"fields": ["site_name", "logo", "accent_color"]}),
        (
            "Слоган і SEO",
            {
                "fields": [
                    "slogan_uk",
                    "slogan_ru",
                    "meta_description_uk",
                    "meta_description_ru",
                ]
            },
        ),
        (
            "Контакти",
            {
                "fields": [
                    "phone",
                    "email",
                    "manager_email",
                    "instagram",
                    "telegram",
                    "viber",
                    "whatsapp",
                    "tiktok",
                    "work_hours_uk",
                    "work_hours_ru",
                ],
                "description": (
                    "URL соцмереж і месенджерів можна змінювати тут. "
                    "Для Viber/WhatsApp можна вказати повний URL або номер телефону."
                ),
            },
        ),
        ("Промо-смуга", {"fields": ["promo_is_active", "promo_text_uk", "promo_text_ru"]}),
        (
            "Hero без банерів",
            {
                "fields": [
                    "hero_title_uk",
                    "hero_title_ru",
                    "hero_subtitle_uk",
                    "hero_subtitle_ru",
                    "hero_button_uk",
                    "hero_button_ru",
                ],
                "description": "Показується на головній, якщо немає активних банерів.",
            },
        ),
        (
            "Блок «Ви косметолог?»",
            {
                "fields": [
                    "pro_cta_title_uk",
                    "pro_cta_title_ru",
                    "pro_cta_text_uk",
                    "pro_cta_text_ru",
                    "pro_cta_button_uk",
                    "pro_cta_button_ru",
                    "pro_cta_image",
                    "pro_cta_image_mobile",
                    "pro_cta_bg_color",
                    "pro_cta_text_color",
                    "pro_cta_button_color",
                    "pro_cta_button_text_color",
                ],
                "description": (
                    "Блок на головній для гостей і звичайних клієнтів (не косметологів). "
                    "Фото — фон на весь блок; мобільне опційне (інакше десктопне)."
                ),
            },
        ),
        (
            "USP-картки",
            {
                "fields": [
                    "usp1_title_uk",
                    "usp1_title_ru",
                    "usp1_text_uk",
                    "usp1_text_ru",
                    "usp2_title_uk",
                    "usp2_title_ru",
                    "usp2_text_uk",
                    "usp2_text_ru",
                    "usp3_title_uk",
                    "usp3_title_ru",
                    "usp3_text_uk",
                    "usp3_text_ru",
                    "usp4_title_uk",
                    "usp4_title_ru",
                    "usp4_text_uk",
                    "usp4_text_ru",
                ]
            },
        ),
        (
            "Реквізити ФОП",
            {"fields": ["bank_recipient", "bank_tax_id", "bank_iban", "bank_name", "bank_purpose_template"]},
        ),
    ]


@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ["title_uk", "slug", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    prepopulated_fields = {"slug": ("title_uk",)}
    search_fields = ["title_uk", "title_ru"]
    rich_fields = {"body_uk", "body_ru", "body_pro_uk", "body_pro_ru"}
    fieldsets = [
        (None, {"fields": ["title_uk", "title_ru", "slug", "is_active", "sort_order"]}),
        ("Текст", {"fields": ["body_uk", "body_ru"]}),
        ("Текст для косметологів", {"fields": ["body_pro_uk", "body_pro_ru"], "classes": ["collapse"]}),
        (
            "SEO",
            {
                "fields": ["seo_title_uk", "seo_title_ru", "seo_description_uk", "seo_description_ru"],
                "classes": ["collapse"],
            },
        ),
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.rich_fields:
            kwargs["widget"] = TinyMCE(mce_attrs={"height": 420})
            return super().formfield_for_dbfield(db_field, request, **kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    list_display = ["title_uk", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    fieldsets = [
        (None, {"fields": ["title_uk", "title_ru", "subtitle_uk", "subtitle_ru"]}),
        (
            "Зображення",
            {
                "fields": ["image", "image_mobile"],
                "description": (
                    "Десктоп — 21:9 (1680×720 або 1920×823). "
                    "Мобільний — 3:4 (900×1200), до 599 px. Формат JPG/WebP."
                ),
            },
        ),
        (
            "Кольори",
            {
                "fields": ["text_color", "button_color", "button_text_color"],
                "description": "Підлаштуйте під фон зображення банера. Формат #RRGGBB.",
            },
        ),
        (
            "Кнопка",
            {
                "fields": ["button_text_uk", "button_text_ru", "button_url"],
                "description": (
                    "Посилання — один шлях для обох мов, без /uk/ чи /ru/ "
                    "(напр. /catalog/syrovatky/). Мовний префікс додається на сайті."
                ),
            },
        ),
        ("Публікація", {"fields": ["is_active", "sort_order"]}),
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in {"text_color", "button_color", "button_text_color"}:
            kwargs["widget"] = HexColorInput()
        return super().formfield_for_dbfield(db_field, request, **kwargs)
