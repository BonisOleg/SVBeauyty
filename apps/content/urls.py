from django.urls import path

from apps.content import views

app_name = "content"

urlpatterns = [
    path("page/<slug:slug>/", views.page, name="page"),
]
