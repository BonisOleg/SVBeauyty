from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import action
from unfold.enums import ActionVariant

from apps.loyalty.forms import AdjustLoyaltyPointsForm
from apps.loyalty.models import LoyaltyAccount, LoyaltySettings, LoyaltyTransaction, TransactionKind
from apps.loyalty.services import apply_transaction, get_available_balance


@admin.register(LoyaltySettings)
class LoyaltySettingsAdmin(ModelAdmin):
    fieldsets = [
        (None, {"fields": ["is_enabled", "earn_for_pro"]}),
        ("Нарахування", {"fields": ["earn_points_per_uah", "earn_hold_days"]}),
        ("Списання", {"fields": ["redeem_uah_per_point", "max_redeem_percent"]}),
    ]

    def has_add_permission(self, request):
        return not LoyaltySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(ModelAdmin):
    list_display = ["user", "balance", "available_balance_display", "updated_at"]
    search_fields = ["user__email"]
    readonly_fields = ["user", "balance", "available_balance_display", "created_at", "updated_at"]
    actions_detail = ["adjust_points"]
    actions_row = ["adjust_points"]

    @admin.display(description=_("Доступно до списання"))
    def available_balance_display(self, obj):
        return get_available_balance(obj.user)

    @action(
        description=_("Змінити бали"),
        url_path="adjust-points",
        permissions=["change"],
        icon="toll",
        variant=ActionVariant.PRIMARY,
    )
    def adjust_points(self, request, object_id):
        account = get_object_or_404(
            LoyaltyAccount.objects.select_related("user"), pk=object_id
        )
        if not self.has_change_permission(request, account):
            raise PermissionDenied

        if request.method == "POST":
            form = AdjustLoyaltyPointsForm(request.POST)
            if form.is_valid():
                points = form.cleaned_data["points"]
                operation = form.cleaned_data["operation"]
                comment = form.cleaned_data["comment"].strip()
                signed = points if operation == AdjustLoyaltyPointsForm.OPERATION_CREDIT else -points
                admin_label = getattr(request.user, "email", "") or request.user.get_username()
                full_comment = f"Адмін {admin_label}: {comment}"
                try:
                    txn = apply_transaction(
                        account.user,
                        TransactionKind.MANUAL,
                        signed,
                        comment=full_comment,
                    )
                except ValueError as exc:
                    form.add_error(None, str(exc))
                else:
                    account.refresh_from_db(fields=["balance"])
                    if signed > 0:
                        self.message_user(
                            request,
                            _("Нараховано %(n)s балів. Баланс: %(b)s.")
                            % {"n": points, "b": account.balance},
                            messages.SUCCESS,
                        )
                    else:
                        self.message_user(
                            request,
                            _("Списано %(n)s балів. Баланс: %(b)s.")
                            % {"n": points, "b": account.balance},
                            messages.SUCCESS,
                        )
                    if txn is None:
                        self.message_user(
                            request,
                            _("Операцію не застосовано."),
                            messages.WARNING,
                        )
                    return redirect("admin:loyalty_loyaltyaccount_change", account.pk)
        else:
            form = AdjustLoyaltyPointsForm(
                initial={"operation": AdjustLoyaltyPointsForm.OPERATION_CREDIT}
            )

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": account,
            "account": account,
            "form": form,
            "title": _("Змінити бали"),
            "available_balance": get_available_balance(account.user),
            "has_view_permission": self.has_view_permission(request, account),
            "has_add_permission": self.has_add_permission(request),
            "has_change_permission": self.has_change_permission(request, account),
            "has_delete_permission": self.has_delete_permission(request, account),
        }
        return TemplateResponse(
            request,
            "admin/loyalty/loyaltyaccount/adjust_points.html",
            context,
        )


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(ModelAdmin):
    list_display = ["created_at", "account", "kind", "points", "balance_after", "order", "comment"]
    list_filter = ["kind", "created_at"]
    search_fields = ["account__user__email", "order__number", "comment"]
    readonly_fields = [
        "account",
        "order",
        "kind",
        "points",
        "balance_after",
        "comment",
        "created_at",
        "updated_at",
    ]
    list_select_related = ["account__user", "order"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
