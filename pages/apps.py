from django.apps import AppConfig


class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'
    verbose_name = 'Сторінки'

    def ready(self):
        # Proxy CMS-моделі мають бути імпортовані для admin/migrations.
        from pages import cms_proxies  # noqa: F401
        from pages.webp_upload import connect_webp_signals

        connect_webp_signals()
