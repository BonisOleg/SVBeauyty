from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.loyalty.models import LoyaltyAccount, LoyaltySettings, LoyaltyTransaction


@admin.register(LoyaltySettings)
class LoyaltySettingsAdmin(ModelAdmin):
    fieldsets = [
        (None, {"fields": ["is_enabled", "earn_for_pro"]}),
        ("Нарахування", {"fields": ["earn_points_per_uah"]}),
        ("Списання", {"fields": ["redeem_uah_per_point", "max_redeem_percent"]}),
    ]

    def has_add_permission(self, request):
        return not LoyaltySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(ModelAdmin):
    list_display = ["user", "balance", "updated_at"]
    search_fields = ["user__email"]
    readonly_fields = ["user", "balance"]


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(ModelAdmin):
    list_display = ["created_at", "account", "kind", "points", "balance_after", "order"]
    list_filter = ["kind", "created_at"]
    search_fields = ["account__user__email", "order__number"]
    readonly_fields = ["balance_after"]
    list_select_related = ["account__user", "order"]
