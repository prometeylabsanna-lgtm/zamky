from django.apps import AppConfig


class MarketingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "marketing"
    verbose_name = "Маркетинг"

    def ready(self):
        from marketing import signals  # noqa: F401
