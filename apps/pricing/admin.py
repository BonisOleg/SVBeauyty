from django.conf import settings
from django.contrib import admin
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from apps.pricing import services
from apps.pricing.models import PricingSettings


@admin.register(PricingSettings)
class PricingSettingsAdmin(ModelAdmin):
    rich_fields = {
        "pro_delivery_note_uk",
        "pro_delivery_note_ru",
        "retail_delivery_note_uk",
        "retail_delivery_note_ru",
    }
    fieldsets = [
        (
            "Націнки",
            {
                "fields": ["retail_markup_percent", "pro_markup_percent", "rounding_step"],
                "description": (
                    "Після збереження ціни всіх товарів перерахуються автоматично. "
                    "Позиції з галочкою «ціна вручну» лишаються без змін."
                ),
            },
        ),
        ("Косметологи", {"fields": ["pro_min_order_uah", "free_delivery_from_pro_uah"]}),
        ("Умови доставки для косметологів", {"fields": ["pro_delivery_note_uk", "pro_delivery_note_ru"]}),
        ("Роздріб", {"fields": ["free_delivery_from_uah", "retail_delivery_note_uk", "retail_delivery_note_ru"]}),
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.rich_fields:
            compact = getattr(settings, "TINYMCE_COMPACT_CONFIG", None) or {}
            kwargs["widget"] = TinyMCE(mce_attrs=compact)
            return super().formfield_for_dbfield(db_field, request, **kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        markup_changed = {"retail_markup_percent", "pro_markup_percent", "rounding_step"} & set(
            form.changed_data
        )
        if markup_changed:
            count = services.recalculate_all()
            self.message_user(request, f"Перераховано цін: {count}.")

    def has_add_permission(self, request):
        return not PricingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
