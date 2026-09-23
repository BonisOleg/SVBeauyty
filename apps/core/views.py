from django.shortcuts import render

from apps.catalog import selectors
from apps.catalog.models import Category
from apps.content.models import Banner

HOME_CATEGORIES_LIMIT = 8


def home(request):
    user = request.user if request.user.is_authenticated else None
    base_qs = selectors.active_products(request.user)
    context = {
        "banners": Banner.objects.filter(is_active=True).order_by("sort_order", "id"),
        "categories": Category.objects.filter(is_active=True).order_by("sort_order", "id")[
            :HOME_CATEGORIES_LIMIT
        ],
        "hits": base_qs.filter(is_hit=True)[:8],
        "novelties": base_qs.filter(is_new=True)[:8],
        "user_for_pricing": user,
    }
    return render(request, "core/home.html", context)


def handler404(request, exception):
    return render(request, "core/404.html", status=404)


def handler500(request):
    return render(request, "core/500.html", status=500)
