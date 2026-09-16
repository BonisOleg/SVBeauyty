from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.core.admin import SingletonAdmin
from apps.core.admin_i18n import bilingual_fieldsets
from apps.shipping.models import ShippingSettings


@admin.register(ShippingSettings)
class ShippingSettingsAdmin(SingletonAdmin):
    fieldsets = bilingual_fieldsets(
        [
            (
                "Нова Пошта",
                {"fields": ["np_api_key", "use_test_data"]},
            ),
            ("Самовивіз", {"fields": ["pickup_enabled"]}),
            ("Таксі", {"fields": ["taxi_enabled"]}),
        ],
        uk_fields=["pickup_address_uk", "pickup_note_uk", "taxi_note_uk"],
        ru_fields=["pickup_address_ru", "pickup_note_ru", "taxi_note_ru"],
    )
