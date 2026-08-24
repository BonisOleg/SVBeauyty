from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.pricing import services
from apps.pricing.models import PricingSettings


@admin.register(PricingSettings)
class PricingSettingsAdmin(ModelAdmin):
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
