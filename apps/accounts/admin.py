from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.accounts.models import ClientType, CosmetologistRequest, RequestStatus, User


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "first_name", "last_name", "phone", "client_type", "is_active"]
    list_editable = ["client_type"]
    list_filter = ["client_type", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        (_("Особисті дані"), {"fields": ["first_name", "last_name", "phone"]}),
        (_("Статус клієнта"), {"fields": ["client_type", "client_type_changed_at"]}),
        (_("Права"), {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
        (_("Дати"), {"fields": ["last_login", "date_joined"], "classes": ["collapse"]}),
    ]
    add_fieldsets = [
        (None, {"classes": ["wide"], "fields": ["email", "password1", "password2", "client_type"]}),
    ]
    readonly_fields = ["client_type_changed_at", "last_login", "date_joined"]

    def save_model(self, request, obj, form, change):
        if change and "client_type" in form.changed_data:
            obj.client_type_changed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(CosmetologistRequest)
class CosmetologistRequestAdmin(ModelAdmin):
    list_display = ["full_name", "user", "phone", "workplace", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["full_name", "phone", "user__email"]
    readonly_fields = ["user", "created_at", "updated_at"]
    actions = ["approve_requests", "reject_requests"]

    @admin.action(description=_("Схвалити: надати статус косметолога"))
    def approve_requests(self, request, queryset):
        count = 0
        for obj in queryset.select_related("user"):
            obj.status = RequestStatus.APPROVED
            obj.save(update_fields=["status", "updated_at"])
            obj.user.client_type = ClientType.COSMETOLOGIST
            obj.user.client_type_changed_at = timezone.now()
            obj.user.save(update_fields=["client_type", "client_type_changed_at"])
            count += 1
        self.message_user(request, f"Схвалено заявок: {count}")

    @admin.action(description=_("Відхилити заявку"))
    def reject_requests(self, request, queryset):
        for obj in queryset.select_related("user"):
            obj.status = RequestStatus.REJECTED
            obj.save(update_fields=["status", "updated_at"])
            if obj.user.client_type == ClientType.PENDING:
                obj.user.client_type = ClientType.REGULAR
                obj.user.save(update_fields=["client_type"])
        self.message_user(request, "Заявки відхилено")
