"""Запити до Product під час старих data-міграцій, до нових колонок."""

from django.db import connection

_OPTIONAL = ('reviews_count', 'warranty_months')


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
