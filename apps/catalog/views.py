import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from apps.catalog import selectors
from apps.catalog import wishlist as wishlist_services
from apps.catalog.models import Category, ProductReview
from apps.catalog.reviews import user_purchased_product


def catalog(request):
    return render(
        request,
        "catalog/catalog.html",
        selectors.catalog_page_context(request, queryset=selectors.active_products()),
    )


def category(request, slug):
    category_obj = get_object_or_404(Category, slug=slug, is_active=True)
    return render(
        request,
        "catalog/catalog.html",
        selectors.catalog_page_context(
            request,
            queryset=selectors.active_products(),
            category=category_obj,
        ),
    )


def product(request, slug):
    product_obj = get_object_or_404(
        selectors.active_products().prefetch_related("images", "reviews"),
        slug=slug,
    )
    recently_viewed = selectors.recently_viewed_products(request, exclude_id=product_obj.pk)
    selectors.touch_recently_viewed(request, product_obj.pk)
    reviews = []
    if settings.REVIEWS_ENABLED:
        reviews = product_obj.reviews.filter(is_published=True).order_by("-created_at")[:50]
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = product_obj.pk in wishlist_services.product_ids_for(request.user)
    return render(
        request,
        "catalog/product.html",
        {
            "product": product_obj,
            "related": selectors.related_products(product_obj),
            "also_bought": selectors.also_bought_products(product_obj),
            "recently_viewed": recently_viewed,
            "in_wishlist": in_wishlist,
            "reviews": reviews,
        },
    )


@login_required
@require_POST
def review_add(request, slug):
    if not settings.REVIEWS_ENABLED:
        raise Http404()
    product_obj = get_object_or_404(selectors.active_products(), slug=slug)
    try:
        rating = int(request.POST.get("rating") or 0)
    except (TypeError, ValueError):
        rating = 0
    author_name = (request.POST.get("author_name") or "").strip()[:120]
    text = (request.POST.get("text") or "").strip()[:2000]
    if rating < 1 or rating > 5 or not author_name:
        messages.error(request, _("Перевірте оцінку та імʼя."))
        return redirect(f"{product_obj.get_absolute_url()}#reviews")

    ProductReview.objects.create(
        product=product_obj,
        user=request.user,
        author_name=author_name,
        rating=rating,
        text=text,
        is_verified_purchase=user_purchased_product(request.user, product_obj),
        is_published=False,
    )
    messages.success(request, _("Дякуємо! Відгук зʼявиться після перевірки модератором."))
    return redirect(f"{product_obj.get_absolute_url()}#reviews")


def search(request):
    query = (request.GET.get("q") or "").strip()
    return render(
        request,
        "catalog/catalog.html",
        selectors.catalog_page_context(
            request,
            queryset=selectors.search_products(query),
            query=query,
            is_search=True,
        ),
    )


@require_POST
def wishlist_toggle(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth_required"}, status=401)
    try:
        product_id = int(request.POST.get("product_id") or 0)
    except (TypeError, ValueError):
        return JsonResponse({"error": "invalid product"}, status=400)
    if product_id <= 0:
        return JsonResponse({"error": "invalid product"}, status=400)
    in_wishlist, count = wishlist_services.toggle(request.user, product_id)
    return JsonResponse(
        {
            "product_id": product_id,
            "in_wishlist": in_wishlist,
            "count": count,
        }
    )


@require_GET
def wishlist_products(request):
    """HTML-картки товарів за ids (для guest localStorage wishlist)."""
    from apps.catalog.product_grid import pick_grid_columns

    raw = request.GET.get("ids", "")
    ids = [part.strip() for part in raw.split(",") if part.strip()]
    products = wishlist_services.list_products_by_ids(ids)
    html = render_to_string(
        "catalog/_wishlist_products.html",
        {"products": products, "wishlist_product_ids": {p.pk for p in products}},
        request=request,
    )
    return JsonResponse(
        {
            "html": html,
            "count": len(products),
            "ids": [p.pk for p in products],
            "grid_cols": pick_grid_columns(len(products)),
        }
    )


@require_POST
@login_required
def wishlist_merge(request):
    """Зливає guest localStorage ids у wishlist користувача."""
    raw = request.POST.get("ids", "")
    try:
        ids = json.loads(raw) if raw.strip().startswith("[") else [
            part.strip() for part in raw.split(",") if part.strip()
        ]
    except (TypeError, ValueError, json.JSONDecodeError):
        ids = []
    count = wishlist_services.merge_ids_for_user(request.user, ids)
    return JsonResponse({"ok": True, "count": count})
