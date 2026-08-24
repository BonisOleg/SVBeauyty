from django.urls import path
from django.utils.translation import pgettext_lazy

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path(pgettext_lazy("url", "catalog/"), views.catalog, name="catalog"),
    path(pgettext_lazy("url", "search/"), views.search, name="search"),
    path(pgettext_lazy("url", "catalog/<slug:slug>/"), views.category, name="category"),
    path(pgettext_lazy("url", "product/<slug:slug>/"), views.product, name="product"),
]
