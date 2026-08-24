from django.shortcuts import get_object_or_404, render

from apps.catalog import selectors
from apps.catalog.models import Category


def catalog(request):
    sort = request.GET.get("sort", "popular")
    queryset = selectors.filter_catalog(
        brands=request.GET.getlist("brand"),
        in_stock=request.GET.get("in_stock") == "1",
        sort=sort,
    )
    return render(
        request,
        "catalog/catalog.html",
        {
            "page_obj": selectors.paginate(request, queryset),
            "categories": selectors.active_categories(),
            "brands": selectors.active_brands(),
            "current_sort": sort,
            "current_brands": request.GET.getlist("brand"),
        },
    )


def category(request, slug):
    category_obj = get_object_or_404(Category, slug=slug, is_active=True)
    sort = request.GET.get("sort", "popular")
    queryset = selectors.filter_catalog(
        category=category_obj,
        brands=request.GET.getlist("brand"),
        in_stock=request.GET.get("in_stock") == "1",
        sort=sort,
    )
    return render(
        request,
        "catalog/catalog.html",
        {
            "category": category_obj,
            "page_obj": selectors.paginate(request, queryset),
            "categories": selectors.active_categories(),
            "brands": selectors.active_brands(),
            "current_sort": sort,
            "current_brands": request.GET.getlist("brand"),
        },
    )


def product(request, slug):
    product_obj = get_object_or_404(selectors.active_products().prefetch_related("images"), slug=slug)
    return render(
        request,
        "catalog/product.html",
        {
            "product": product_obj,
            "related": selectors.related_products(product_obj),
        },
    )


def search(request):
    query = (request.GET.get("q") or "").strip()
    queryset = selectors.search_products(query)
    return render(
        request,
        "catalog/catalog.html",
        {
            "query": query,
            "page_obj": selectors.paginate(request, queryset),
            "categories": selectors.active_categories(),
            "brands": selectors.active_brands(),
            "current_sort": "popular",
            "current_brands": [],
            "is_search": True,
        },
    )
