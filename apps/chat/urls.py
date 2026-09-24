from django.urls import path

from apps.chat import views

app_name = "chat"

urlpatterns = [
    path("history/", views.history, name="history"),
    path("send/", views.send, name="send"),
    path("file/<uuid:public_id>/", views.attachment_file, name="file"),
]
