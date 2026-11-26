from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'
    verbose_name = 'Каталог'

    def ready(self):
        from catalog.review_stats import connect_review_signals
        from config.local_schema import autmigrate_sqlite

        autmigrate_sqlite()
        connect_review_signals()
