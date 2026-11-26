"""Запити до Product під час старих data-міграцій, до нових колонок/таблиць."""

from django.db import connection
from django.db.utils import OperationalError, ProgrammingError

_OPTIONAL = ('reviews_count', 'warranty_months')
_review_ready = None


def reset_schema_cache():
    global _review_ready
    _review_ready = None


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


def product_qs():
    from catalog.models import Product

    missing = missing_product_columns()
    qs = Product.objects.all()
    if missing:
        qs = qs.defer(*missing)
    return qs
