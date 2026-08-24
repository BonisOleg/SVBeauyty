from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.shipping.models import ShippingSettings


@admin.register(ShippingSettings)
class ShippingSettingsAdmin(ModelAdmin):
    fields = ["np_api_key", "use_test_data"]

    def has_add_permission(self, request):
        return not ShippingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
