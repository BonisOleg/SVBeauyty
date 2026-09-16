"""Спільні mixin-и для Django admin."""

from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin


class SingletonAdmin(ModelAdmin):
    """Модель з одним записом: changelist одразу відкриває форму редагування."""

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.objects.order_by("pk").first()
        opts = self.model._meta
        if obj is not None:
            return redirect(
                reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk])
            )
        if self.has_add_permission(request):
            return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_add"))
        return super().changelist_view(request, extra_context=extra_context)
