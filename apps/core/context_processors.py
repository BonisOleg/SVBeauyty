from django.conf import settings

from apps.catalog.models import Category
from apps.content.models import SiteSettings


def site_context(request):
    settings_obj = SiteSettings.get_solo()
    return {
        "site_settings": settings_obj,
        "menu_categories": Category.objects.filter(is_active=True).order_by("sort_order", "id"),
        "is_pro_user": getattr(request.user, "is_pro", False),
        "reviews_enabled": bool(settings.REVIEWS_ENABLED),
    }
