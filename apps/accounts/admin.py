from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Case, IntegerField, Value, When
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.accounts.models import ClientType, CosmetologistRequest, RequestStatus, User
from apps.core.admin_list_markers import mark_new, new_badge


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
    list_display = ["full_name_display", "user", "phone", "workplace", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["full_name", "phone", "user__email"]
    fields = [
        "user",
        "full_name",
        "phone",
        "workplace",
        "document_link",
        "comment",
        "status",
        "admin_note",
        "created_at",
        "updated_at",
    ]
    readonly_fields = ["user", "document_link", "created_at", "updated_at"]
    actions = ["approve_requests", "reject_requests"]

    @admin.display(description=_("Документ"))
    def document_link(self, obj):
        if not obj or not obj.pk or not obj.document:
            return "—"
        url = reverse("cosmetologist_document", args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, _("Відкрити документ"))

    @admin.display(description=_("ПІБ"), ordering="full_name")
    def full_name_display(self, obj):
        label = format_html('<span class="admin-list-title">{}</span>', obj.full_name)
        if obj.status == RequestStatus.NEW:
            return mark_new(format_html("{}{}", new_badge(), label))
        return label

    def get_ordering(self, request):
        return ("_is_new", "-created_at")

    def get_queryset(self, request):
        qs = self.model._default_manager.get_queryset()
        return qs.annotate(
            _is_new=Case(
                When(status=RequestStatus.NEW, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )

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
