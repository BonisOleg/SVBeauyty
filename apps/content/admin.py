from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.content.models import Banner, Page, SiteSettings


class SingletonAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdmin):
    fieldsets = [
        ("Бренд", {"fields": ["site_name", "logo", "accent_color"]}),
        (
            "Контакти",
            {
                "fields": [
                    "phone",
                    "email",
                    "manager_email",
                    "viber",
                    "telegram",
                    "whatsapp",
                    "instagram",
                    "work_hours_uk",
                    "work_hours_ru",
                ]
            },
        ),
        ("Промо-смуга", {"fields": ["promo_is_active", "promo_text_uk", "promo_text_ru"]}),
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
        ("Кнопка", {"fields": ["button_text_uk", "button_text_ru", "button_url"]}),
        ("Публікація", {"fields": ["is_active", "sort_order"]}),
    ]
