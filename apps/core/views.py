from django.shortcuts import render

from apps.catalog.models import Category, Product
from apps.content.models import Banner


def home(request):
    user = request.user if request.user.is_authenticated else None
    base_qs = (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related("variants", "images")
    )
    context = {
        "banners": Banner.objects.filter(is_active=True).order_by("sort_order", "id"),
        "categories": Category.objects.filter(is_active=True).order_by("sort_order", "id"),
        "hits": base_qs.filter(is_hit=True)[:8],
        "novelties": base_qs.filter(is_new=True)[:8],
        "user_for_pricing": user,
    }
    return render(request, "core/home.html", context)


def handler404(request, exception):
    return render(request, "core/404.html", status=404)


def handler500(request):
    return render(request, "core/500.html", status=500)
