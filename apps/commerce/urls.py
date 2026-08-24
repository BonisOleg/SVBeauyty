from django.urls import path
from django.utils.translation import pgettext_lazy

from apps.commerce import views

app_name = "commerce"

urlpatterns = [
    path(pgettext_lazy("url", "cart/"), views.cart, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/", views.cart_remove, name="cart_remove"),
    path(pgettext_lazy("url", "checkout/"), views.checkout, name="checkout"),
    path(pgettext_lazy("url", "thanks/<str:number>/"), views.thanks, name="thanks"),
]
