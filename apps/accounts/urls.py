from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("cabinet/login/", views.CabinetLoginView.as_view(), name="login"),
    path("cabinet/register/", views.register, name="register"),
    path("cabinet/logout/", views.logout_view, name="logout"),
    path("cabinet/", views.profile, name="profile"),
    path("cabinet/orders/", views.orders, name="orders"),
    path("cabinet/orders/<str:number>/", views.order_detail, name="order_detail"),
    path("cabinet/loyalty/", views.loyalty_history, name="loyalty"),
    path("cabinet/wishlist/", views.wishlist, name="wishlist"),
    path("cabinet/cosmetologist/", views.cosmetologist_request, name="cosmetologist"),
]
