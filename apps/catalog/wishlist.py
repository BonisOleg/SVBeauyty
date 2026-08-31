from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from apps.catalog.models import Product, Variant, WishlistItem


def _product_queryset():
    return Product.objects.filter(is_active=True).select_related("brand", "category").prefetch_related(
        Prefetch(
            "variants",
            queryset=Variant.objects.filter(is_active=True).order_by("sort_order", "id"),
        ),
        "images",
    )


def product_ids_for(user) -> set[int]:
    if not getattr(user, "is_authenticated", False):
        return set()
    return set(WishlistItem.objects.filter(user=user).values_list("product_id", flat=True))


def count_for(user) -> int:
    if not getattr(user, "is_authenticated", False):
        return 0
    return WishlistItem.objects.filter(user=user).count()


def list_products_for(user):
    items = (
        WishlistItem.objects.filter(user=user, product__is_active=True)
        .select_related("product__brand", "product__category")
        .prefetch_related(
            Prefetch(
                "product__variants",
                queryset=Variant.objects.filter(is_active=True).order_by("sort_order", "id"),
            ),
            "product__images",
        )
        .order_by("-created_at")
    )
    return [item.product for item in items]


def list_products_by_ids(ids: list[int]):
    """Зберігає порядок ids (для guest localStorage)."""
    cleaned = []
    seen = set()
    for raw in ids:
        try:
            pk = int(raw)
        except (TypeError, ValueError):
            continue
        if pk <= 0 or pk in seen:
            continue
        seen.add(pk)
        cleaned.append(pk)
    if not cleaned:
        return []
    products = {p.pk: p for p in _product_queryset().filter(pk__in=cleaned)}
    return [products[pk] for pk in cleaned if pk in products]


@transaction.atomic
def toggle(user, product_id: int) -> tuple[bool, int]:
    """Додає або прибирає товар. Повертає (in_wishlist, count)."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    existing = WishlistItem.objects.filter(user=user, product=product).first()
    if existing:
        existing.delete()
        return False, count_for(user)
    try:
        WishlistItem.objects.create(user=user, product=product)
    except IntegrityError:
        pass
    return True, count_for(user)


@transaction.atomic
def merge_ids_for_user(user, ids: list[int]) -> int:
    """Додає товари з guest-списку в БД. Повертає новий count."""
    if not getattr(user, "is_authenticated", False):
        return 0
    for product in list_products_by_ids(ids):
        try:
            WishlistItem.objects.get_or_create(user=user, product=product)
        except IntegrityError:
            continue
    return count_for(user)
