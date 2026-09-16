from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Загальне"

    def ready(self) -> None:
        from apps.core.signals_images import connect_webp_signals

        connect_webp_signals()

