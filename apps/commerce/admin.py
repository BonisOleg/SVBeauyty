from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.commerce.models import Cart, CartItem, Order, OrderItem, OrderStatusLog


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    fields = [
        "product_name",
        "sku",
        "volume",
        "unit_purchase_price_uah",
        "unit_price_uah",
        "price_source",
        "quantity",
        "line_total_uah",
        "margin",
    ]
    readonly_fields = ["line_total_uah", "margin"]

    @admin.display(description="Маржа, грн")
    def margin(self, obj):
        value = obj.margin_uah
        return "—" if value is None else f"{value:g}"


class OrderStatusLogInline(TabularInline):
    model = OrderStatusLog
    extra = 0
    fields = ["old_status", "new_status", "changed_by", "created_at"]
    readonly_fields = fields
    can_delete = False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ["number", "created_at", "customer_name", "phone", "client_type", "total_uah", "status"]
    list_editable = ["status"]
    list_filter = ["status", "payment_method", "delivery_method", "client_type", "created_at"]
    search_fields = [
        "number",
        "phone",
        "email",
        "first_name",
        "last_name",
        "recipient_first_name",
        "recipient_last_name",
        "recipient_phone",
    ]
    inlines = [OrderItemInline, OrderStatusLogInline]
    readonly_fields = ["number", "subtotal_uah", "total_uah", "bank_details_snapshot", "created_at"]
    fieldsets = [
        (None, {"fields": ["number", "status", "created_at"]}),
        ("Клієнт", {"fields": ["user", "client_type", "first_name", "last_name", "phone", "email"]}),
        (
            "Отримувач",
            {
                "fields": [
                    "other_recipient",
                    "recipient_first_name",
                    "recipient_last_name",
                    "recipient_phone",
                ]
            },
        ),
        (
            "Доставка",
            {
                "fields": [
                    "delivery_method",
                    "delivery_city",
                    "delivery_city_ref",
                    "delivery_branch",
                    "delivery_branch_ref",
                    "delivery_address",
                ]
            },
        ),
        ("Оплата", {"fields": ["payment_method", "bank_details_snapshot"]}),
        (
            "Суми",
            {"fields": ["subtotal_uah", "loyalty_spent_points", "loyalty_discount_uah", "total_uah"]},
        ),
        ("Інше", {"fields": ["comment", "gdpr_accepted", "locale"]}),
    ]

    def save_model(self, request, obj, form, change):
        old_status = ""
        if change:
            old_status = Order.objects.get(pk=obj.pk).status
        super().save_model(request, obj, form, change)
        if change and old_status != obj.status:
            OrderStatusLog.objects.create(
                order=obj, old_status=old_status, new_status=obj.status, changed_by=request.user
            )

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model is OrderItem:
            form.instance.recalculate()
            form.instance.save(update_fields=["subtotal_uah", "total_uah", "updated_at"])


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ["variant", "quantity"]
    can_delete = False


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ["id", "user", "status", "updated_at"]
    list_filter = ["status"]
    inlines = [CartItemInline]
    readonly_fields = ["session_key", "user", "created_at", "updated_at"]
