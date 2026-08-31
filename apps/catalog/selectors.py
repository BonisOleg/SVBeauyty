from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Avg, Count, Prefetch, Q, QuerySet

from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductAttributeGroup,
    Variant,
)

PER_PAGE = 24

SORT_MAP = {
    "popular": ["sort_order", "-created_at"],
    "new": ["-created_at"],
    "name": ["name_uk"],
}

ATTRIBUTE_FILTER_KEYS = (
    ProductAttributeGroup.Slug.AGE,
    ProductAttributeGroup.Slug.SKIN_TYPE,
    ProductAttributeGroup.Slug.SKIN_CONDITION,
    ProductAttributeGroup.Slug.INGREDIENT,
)


def active_products() -> QuerySet[Product]:
    return (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch("variants", queryset=Variant.objects.filter(is_active=True).order_by("sort_order", "id")),
            "images",
            "filter_attrs__group",
        )
        .annotate(
            _rating_avg=Avg("reviews__rating", filter=Q(reviews__is_published=True)),
            _rating_count=Count("reviews", filter=Q(reviews__is_published=True), distinct=True),
        )
    )


def active_categories() -> QuerySet[Category]:
    return Category.objects.filter(is_active=True).order_by("sort_order", "id")


def active_brands() -> QuerySet[Brand]:
    return Brand.objects.filter(is_active=True).order_by("sort_order", "name")


def _parse_price(raw: str | None) -> Decimal | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        value = Decimal(str(raw).replace(",", ".").strip())
    except (InvalidOperation, ValueError):
        return None
    return value if value >= 0 else None


def parse_catalog_filters(request) -> dict:
    attr_filters = {
        key: request.GET.getlist(key) for key in ATTRIBUTE_FILTER_KEYS if request.GET.getlist(key)
    }
    return {
        "brands": request.GET.getlist("brand"),
        "in_stock": request.GET.get("in_stock") == "1",
        "sort": request.GET.get("sort", "popular"),
        "price_min": _parse_price(request.GET.get("price_min")),
        "price_max": _parse_price(request.GET.get("price_max")),
        "attr_filters": attr_filters,
    }


def filter_catalog(
    qs: QuerySet[Product] | None = None,
    *,
    category: Category | None = None,
    brands: list[str] | None = None,
    in_stock: bool = False,
    sort: str = "popular",
    price_min: Decimal | None = None,
    price_max: Decimal | None = None,
    attr_filters: dict[str, list[str]] | None = None,
) -> QuerySet[Product]:
    qs = qs if qs is not None else active_products()
    if category is not None:
        qs = qs.filter(category=category)
    if brands:
        qs = qs.filter(brand__slug__in=brands)
    if in_stock:
        qs = qs.filter(variants__stock_qty__gt=0, variants__is_active=True).distinct()

    price_q = Q(variants__is_active=True)
    if price_min is not None:
        price_q &= Q(variants__price_uah__gte=price_min)
    if price_max is not None:
        price_q &= Q(variants__price_uah__lte=price_max)
    if price_min is not None or price_max is not None:
        qs = qs.filter(price_q).distinct()

    if attr_filters:
        for group_slug, value_slugs in attr_filters.items():
            if not value_slugs:
                continue
            qs = qs.filter(
                filter_attrs__group__slug=group_slug,
                filter_attrs__slug__in=value_slugs,
                filter_attrs__is_active=True,
            ).distinct()

    return qs.order_by(*SORT_MAP.get(sort, SORT_MAP["popular"]))


def filter_groups_for_catalog() -> list[dict]:
    """Групи з значеннями, що реально призначені активним товарам."""
    used_ids = (
        ProductAttribute.objects.filter(
            is_active=True,
            products__is_active=True,
        )
        .values_list("id", flat=True)
        .distinct()
    )
    groups = (
        ProductAttributeGroup.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "attributes",
                queryset=ProductAttribute.objects.filter(is_active=True, id__in=used_ids).order_by(
                    "sort_order", "name_uk"
                ),
            )
        )
        .order_by("sort_order", "id")
    )
    result = []
    for group in groups:
        attrs = list(group.attributes.all())
        if attrs:
            result.append({"group": group, "attributes": attrs})
    return result


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


def related_products(product: Product, limit: int = 8) -> QuerySet[Product]:
    return active_products().filter(category=product.category).exclude(pk=product.pk)[:limit]


def also_bought_products(product: Product, limit: int = 8) -> list[Product]:
    same_brand = list(
        active_products()
        .filter(brand=product.brand)
        .exclude(pk=product.pk)
        .order_by("-is_hit", "sort_order", "-created_at")[:limit]
    )
    if len(same_brand) >= limit:
        return same_brand
    exclude_ids = {product.pk, *(p.pk for p in same_brand)}
    fillers = list(
        active_products()
        .exclude(pk__in=exclude_ids)
        .order_by("-is_hit", "sort_order", "-created_at")[: limit - len(same_brand)]
    )
    return same_brand + fillers


RECENTLY_VIEWED_SESSION_KEY = "recently_viewed_ids"
RECENTLY_VIEWED_LIMIT = 16


def touch_recently_viewed(request, product_id: int) -> None:
    ids = [int(x) for x in request.session.get(RECENTLY_VIEWED_SESSION_KEY, []) if str(x).isdigit()]
    ids = [i for i in ids if i != product_id]
    ids.insert(0, product_id)
    request.session[RECENTLY_VIEWED_SESSION_KEY] = ids[:RECENTLY_VIEWED_LIMIT]
    request.session.modified = True


def recently_viewed_products(request, *, exclude_id: int | None = None, limit: int = 8) -> list[Product]:
    raw = [int(x) for x in request.session.get(RECENTLY_VIEWED_SESSION_KEY, []) if str(x).isdigit()]
    ids = [i for i in raw if exclude_id is None or i != exclude_id][:limit]
    if not ids:
        return []
    found = {
        p.pk: p
        for p in active_products().filter(pk__in=ids)
    }
    return [found[i] for i in ids if i in found]


def paginate(request, queryset, per_page: int = PER_PAGE):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def catalog_page_context(request, *, queryset, category=None, query="", is_search=False) -> dict:
    filters = parse_catalog_filters(request)
    filtered = filter_catalog(
        queryset,
        category=category,
        brands=filters["brands"],
        in_stock=filters["in_stock"],
        sort=filters["sort"],
        price_min=filters["price_min"],
        price_max=filters["price_max"],
        attr_filters=filters["attr_filters"],
    )
    return {
        "page_obj": paginate(request, filtered),
        "categories": active_categories(),
        "brands": active_brands(),
        "filter_groups": filter_groups_for_catalog(),
        "current_sort": filters["sort"],
        "current_brands": filters["brands"],
        "current_attrs": filters["attr_filters"],
        "current_attr_keys": [
            f"{group}:{slug}"
            for group, slugs in filters["attr_filters"].items()
            for slug in slugs
        ],
        "price_min": request.GET.get("price_min", ""),
        "price_max": request.GET.get("price_max", ""),
        "category": category,
        "query": query,
        "is_search": is_search,
    }
