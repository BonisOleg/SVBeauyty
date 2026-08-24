from django.core.paginator import Paginator
from django.db.models import Prefetch, Q, QuerySet

from apps.catalog.models import Brand, Category, Product, Variant

PER_PAGE = 24

SORT_MAP = {
    "popular": ["sort_order", "-created_at"],
    "new": ["-created_at"],
    "name": ["name_uk"],
}


def active_products() -> QuerySet[Product]:
    return (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("variants", queryset=Variant.objects.filter(is_active=True).order_by("sort_order", "id")),
            "images",
        )
    )


def active_categories() -> QuerySet[Category]:
    return Category.objects.filter(is_active=True).order_by("sort_order", "id")


def active_brands() -> QuerySet[Brand]:
    return Brand.objects.filter(is_active=True).order_by("sort_order", "name")


def filter_catalog(
    qs: QuerySet[Product] | None = None,
    *,
    category: Category | None = None,
    brands: list[str] | None = None,
    in_stock: bool = False,
    sort: str = "popular",
) -> QuerySet[Product]:
    qs = qs if qs is not None else active_products()
    if category is not None:
        qs = qs.filter(category=category)
    if brands:
        qs = qs.filter(brand__slug__in=brands)
    if in_stock:
        qs = qs.filter(variants__stock_qty__gt=0, variants__is_active=True).distinct()
    return qs.order_by(*SORT_MAP.get(sort, SORT_MAP["popular"]))


def search_products(query: str) -> QuerySet[Product]:
    query = (query or "").strip()
    if len(query) < 2:
        return active_products().none()
    return (
        active_products()
        .filter(
            Q(name_uk__icontains=query)
            | Q(name_ru__icontains=query)
            | Q(variants__sku__icontains=query)
            | Q(brand__name__icontains=query)
        )
        .distinct()
    )


def get_product_by_slug(slug: str) -> Product:
    return active_products().prefetch_related("images").get(slug=slug, is_active=True)


def related_products(product: Product, limit: int = 4) -> QuerySet[Product]:
    return active_products().filter(category=product.category).exclude(pk=product.pk)[:limit]


def paginate(request, queryset, per_page: int = PER_PAGE):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))
