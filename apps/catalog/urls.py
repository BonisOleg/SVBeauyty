from django.urls import path
from django.utils.translation import pgettext_lazy

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path(pgettext_lazy("url", "catalog/"), views.catalog, name="catalog"),
    path(pgettext_lazy("url", "search/"), views.search, name="search"),
    path("search/suggest/", views.search_suggest, name="search_suggest"),
    path(pgettext_lazy("url", "catalog/<slug:slug>/"), views.category, name="category"),
    path(pgettext_lazy("url", "product/<slug:slug>/"), views.product, name="product"),
    path(
        pgettext_lazy("url", "product/<slug:slug>/review/"),
        views.review_add,
        name="review_add",
    ),
    path("wishlist/toggle/", views.wishlist_toggle, name="wishlist_toggle"),
    path("wishlist/products/", views.wishlist_products, name="wishlist_products"),
    path("wishlist/merge/", views.wishlist_merge, name="wishlist_merge"),
]
