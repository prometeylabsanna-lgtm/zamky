"""Запити до Product під час старих data-міграцій, до нових колонок/таблиць."""

from django.db import connection
from django.db.utils import OperationalError, ProgrammingError

_OPTIONAL = ('reviews_count', 'warranty_months')
_review_ready = None


def reset_schema_cache():
    global _review_ready
    _review_ready = None
    _category_ready_dbs.clear()


def table_exists(name: str) -> bool:
    try:
        return name in connection.introspection.table_names()
    except Exception:
        return False


def review_table_ready() -> bool:
    global _review_ready
    if _review_ready is True:
        return True
    _review_ready = table_exists('catalog_review')
    return _review_ready


def published_reviews_for(product):
    from catalog.models import Review

    if not review_table_ready():
        return []
    try:
        return list(
            Review.objects.filter(product=product, is_published=True).order_by(
                '-created_at', '-id'
            )
        )
    except (OperationalError, ProgrammingError):
        return []


def missing_product_columns():
    try:
        with connection.cursor() as cursor:
            cols = {
                col.name
                for col in connection.introspection.get_table_description(
                    cursor, 'catalog_product'
                )
            }
    except Exception:
        return frozenset()
    return frozenset(name for name in _OPTIONAL if name not in cols)


_category_ready_dbs = set()


def missing_category_columns():
    """Колонки моделі, яких ще немає в таблиці (старі data-міграції)."""
    db_name = str(connection.settings_dict.get("NAME") or "")
    if db_name in _category_ready_dbs:
        return frozenset()
    from django.apps import apps

    if not apps.ready:
        return frozenset()
    from catalog.models import Category

    table = Category._meta.db_table
    if not table_exists(table):
        return frozenset()
    try:
        with connection.cursor() as cursor:
            cols = {
                col.name
                for col in connection.introspection.get_table_description(
                    cursor, table
                )
            }
    except Exception:
        return frozenset()
    missing = frozenset(
        field.name
        for field in Category._meta.local_concrete_fields
        if not field.primary_key and field.column not in cols
    )
    if not missing:
        _category_ready_dbs.add(db_name)
    return missing


def product_qs():
    from catalog.models import Product

    missing = missing_product_columns()
    qs = Product.objects.all()
    if missing:
        qs = qs.defer(*missing)
    return qs
