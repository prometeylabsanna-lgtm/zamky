from django.apps import AppConfig


class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'

    def ready(self):
        # Proxy CMS-моделі мають бути імпортовані для admin/migrations.
        from pages import cms_proxies  # noqa: F401
