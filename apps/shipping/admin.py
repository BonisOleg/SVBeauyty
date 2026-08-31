from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.shipping.models import ShippingSettings


@admin.register(ShippingSettings)
class ShippingSettingsAdmin(ModelAdmin):
    fieldsets = [
        (
            "Нова Пошта",
            {"fields": ["np_api_key", "use_test_data"]},
        ),
        (
            "Самовивіз",
            {
                "fields": [
                    "pickup_enabled",
                    "pickup_address_uk",
                    "pickup_address_ru",
                    "pickup_note_uk",
                    "pickup_note_ru",
                ]
            },
        ),
        (
            "Таксі",
            {"fields": ["taxi_enabled", "taxi_note_uk", "taxi_note_ru"]},
        ),
    ]

    def has_add_permission(self, request):
        return not ShippingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
