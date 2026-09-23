from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import (
    Avg,
    Case,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    IntegerField,
    Max,
    Min,
    Prefetch,
    Q,
    QuerySet,
    Value,
    When,
)

from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductAttributeGroup,
    Variant,
)
from apps.pricing.services import get_global_sale_state, is_pro


PER_PAGE = 24

SORT_MAP = {
    "popular": ["sort_order", "-created_at"],
    "new": ["-created_at"],
    "name": ["name_uk"],
    "price_asc": ["_sort_price", "sort_order", "id"],
    "price_desc": ["-_sort_price", "sort_order", "id"],
}

PRICE_SORTS = frozenset({"price_asc", "price_desc"})
ALLOWED_SORTS = frozenset(SORT_MAP)

ATTRIBUTE_FILTER_KEYS = (
    ProductAttributeGroup.Slug.AGE,
    ProductAttributeGroup.Slug.SKIN_TYPE,
    ProductAttributeGroup.Slug.SKIN_CONDITION,
    ProductAttributeGroup.Slug.INGREDIENT,
)


def active_products(user=None) -> QuerySet[Product]:
    qs = Product.objects.filter(is_active=True)
    if not is_pro(user):
        qs = qs.filter(pro_only=False)
    return (
        qs
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
        "sort": (
            sort
            if (sort := request.GET.get("sort", "popular")) in ALLOWED_SORTS
            else "popular"
        ),
        "price_min": _parse_price(request.GET.get("price_min")),
        "price_max": _parse_price(request.GET.get("price_max")),
        "attr_filters": attr_filters,
    }


def _personal_sale_price_q(
    base: Q,
    *,
    price_min: Decimal | None,
    price_max: Decimal | None,
) -> Q:
    sale_active = Q(variants__sale_price_uah__gt=0) & Q(
        variants__sale_price_uah__lt=F("variants__price_uah")
    )
    no_sale = Q(variants__sale_price_uah__lte=0) | Q(
        variants__sale_price_uah__gte=F("variants__price_uah")
    )
    sale_q = base & sale_active
    retail_q = base & no_sale
    if price_min is not None:
        sale_q &= Q(variants__sale_price_uah__gte=price_min)
        retail_q &= Q(variants__price_uah__gte=price_min)
    if price_max is not None:
        sale_q &= Q(variants__sale_price_uah__lte=price_max)
        retail_q &= Q(variants__price_uah__lte=price_max)
    return sale_q | retail_q


def _price_range_q(
    *,
    price_min: Decimal | None,
    price_max: Decimal | None,
    user=None,
) -> Q:
    """Діапазон за ефективною вітриною ціною (як get_price)."""
    base = Q(variants__is_active=True)
    if is_pro(user):
        q = base
        if price_min is not None:
            q &= Q(variants__price_pro_uah__gte=price_min)
        if price_max is not None:
            q &= Q(variants__price_pro_uah__lte=price_max)
        return q

    state = get_global_sale_state()
    if not state.is_live or state.factor <= 0:
        return _personal_sale_price_q(base, price_min=price_min, price_max=price_max)

    excluded = Q()
    if state.exclude_product_ids:
        excluded |= Q(pk__in=state.exclude_product_ids)
    if state.exclude_brand_ids:
        excluded |= Q(brand_id__in=state.exclude_brand_ids)

    # Inverse of retail * factor (без точного step — похибка на межі ≈ крок округлення).
    global_q = base & ~excluded if excluded else base
    if price_min is not None:
        global_q &= Q(variants__price_uah__gte=(price_min / state.factor))
    if price_max is not None:
        global_q &= Q(variants__price_uah__lte=(price_max / state.factor))

    if not excluded:
        return global_q
    personal_q = _personal_sale_price_q(base & excluded, price_min=price_min, price_max=price_max)
    return global_q | personal_q


def _personal_sale_amount_expr():
    """Ефективна ціна варіанта без global sale (sale якщо активна, інакше retail)."""
    return Case(
        When(
            Q(variants__sale_price_uah__gt=0)
            & Q(variants__sale_price_uah__lt=F("variants__price_uah")),
            then=F("variants__sale_price_uah"),
        ),
        default=F("variants__price_uah"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def _annotate_sort_price(qs: QuerySet[Product], user=None) -> QuerySet[Product]:
    """Мін. вітринна ціна товару для сортування (як get_price, без кроку округлення global)."""
    active = Q(variants__is_active=True)
    if is_pro(user):
        return qs.annotate(
            _sort_price=Min("variants__price_pro_uah", filter=active),
        )

    state = get_global_sale_state()
    personal = _personal_sale_amount_expr()
    if not state.is_live or state.factor <= 0:
        return qs.annotate(_sort_price=Min(personal, filter=active))

    excluded = Q()
    if state.exclude_product_ids:
        excluded |= Q(pk__in=state.exclude_product_ids)
    if state.exclude_brand_ids:
        excluded |= Q(brand_id__in=state.exclude_brand_ids)

    # Global: retail * factor; excluded products — personal sale.
    global_amount = ExpressionWrapper(
        F("variants__price_uah") * Value(state.factor),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    if excluded:
        effective = Case(
            When(excluded, then=personal),
            default=global_amount,
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    else:
        effective = global_amount
    return qs.annotate(_sort_price=Min(effective, filter=active))


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
    user=None,
) -> QuerySet[Product]:
    qs = qs if qs is not None else active_products(user)
    if category is not None:
        qs = qs.filter(category=category)
    if brands:
        qs = qs.filter(brand__slug__in=brands)
    if in_stock:
        qs = qs.filter(variants__stock_qty__gt=0, variants__is_active=True).distinct()

    if price_min is not None or price_max is not None:
        qs = qs.filter(_price_range_q(price_min=price_min, price_max=price_max, user=user)).distinct()

    if attr_filters:
        for group_slug, value_slugs in attr_filters.items():
            if not value_slugs:
                continue
            qs = qs.filter(
                filter_attrs__group__slug=group_slug,
                filter_attrs__slug__in=value_slugs,
                filter_attrs__is_active=True,
            ).distinct()

    sort_key = sort if sort in ALLOWED_SORTS else "popular"
    if sort_key in PRICE_SORTS:
        qs = _annotate_sort_price(qs, user=user)
    return qs.order_by(*SORT_MAP[sort_key])


def filter_groups_for_catalog(user=None) -> list[dict]:
    """Групи з значеннями, що реально призначені видимим товарам."""
    used = ProductAttribute.objects.filter(
        is_active=True,
        products__is_active=True,
    )
    if not is_pro(user):
        used = used.filter(products__pro_only=False)
    used_ids = (
        used
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


def normalize_search_query(query: str | None) -> str:
    return " ".join((query or "").split()).strip()


def search_products(query: str, user=None) -> QuerySet[Product]:
    query = normalize_search_query(query)
    if len(query) < 2:
        return active_products(user).none()
    match = (
        Q(name_uk__icontains=query)
        | Q(name_ru__icontains=query)
        | Q(short_description_uk__icontains=query)
        | Q(short_description_ru__icontains=query)
        | Q(variants__sku__icontains=query)
        | Q(brand__name__icontains=query)
        | Q(category__name_uk__icontains=query)
        | Q(category__name_ru__icontains=query)
    )
    rank = Case(
        When(variants__sku__iexact=query, then=Value(100)),
        When(variants__sku__istartswith=query, then=Value(90)),
        When(name_uk__iexact=query, then=Value(80)),
        When(name_ru__iexact=query, then=Value(78)),
        When(name_uk__istartswith=query, then=Value(70)),
        When(name_ru__istartswith=query, then=Value(68)),
        When(brand__name__iexact=query, then=Value(55)),
        When(brand__name__istartswith=query, then=Value(50)),
        When(category__name_uk__icontains=query, then=Value(35)),
        When(category__name_ru__icontains=query, then=Value(35)),
        default=Value(10),
        output_field=IntegerField(),
    )
    return (
        active_products(user)
        .filter(match)
        .annotate(_search_rank=Max(rank))
        .order_by("-_search_rank", "sort_order", "-created_at", "id")
        .distinct()
    )


def search_suggest_products(query: str, *, limit: int = 8, user=None) -> list[Product]:
    return list(search_products(query, user)[:limit])


def get_product_by_slug(slug: str, user=None) -> Product:
    return active_products(user).prefetch_related("images").get(slug=slug, is_active=True)


def related_products(product: Product, limit: int = 8, user=None) -> QuerySet[Product]:
    return active_products(user).filter(category=product.category).exclude(pk=product.pk)[:limit]


def also_bought_products(product: Product, limit: int = 8, user=None) -> list[Product]:
    same_brand = list(
        active_products(user)
        .filter(brand=product.brand)
        .exclude(pk=product.pk)
        .order_by("-is_hit", "sort_order", "-created_at")[:limit]
    )
    if len(same_brand) >= limit:
        return same_brand
    exclude_ids = {product.pk, *(p.pk for p in same_brand)}
    fillers = list(
        active_products(user)
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
        for p in active_products(request.user).filter(pk__in=ids)
    }
    return [found[i] for i in ids if i in found]


def paginate(request, queryset, per_page: int = PER_PAGE):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def catalog_filters_reset_url(request, *, query: str = "") -> str:
    """Скидання фасетів; на пошуку зберігає q."""
    path = request.path
    query = normalize_search_query(query)
    if query:
        return f"{path}?{urlencode({'q': query})}"
    return path


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
        user=getattr(request, "user", None),
    )
    return {
        "page_obj": paginate(request, filtered),
        "categories": active_categories(),
        "brands": active_brands(),
        "filter_groups": filter_groups_for_catalog(user=getattr(request, "user", None)),
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
        "filters_reset_url": catalog_filters_reset_url(request, query=query),
        "category": category,
        "query": query,
        "is_search": is_search,
        "query_too_short": bool(query) and len(query) < 2,
        "search_empty_query": is_search and not query,
    }
