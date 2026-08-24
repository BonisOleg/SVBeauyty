from django.urls import path

from apps.shipping import views

app_name = "shipping"

urlpatterns = [
    path("cities/", views.cities, name="cities"),
    path("branches/", views.branches, name="branches"),
]
