"""Характеристики на сторінці товару.

Артикул, довжина, A×B і покриття беруться з полів картки товару
(варіанти / кошик). Решта рядків — з обраних фільтрів.
"""

from .models import AttributeGroup

PRODUCT_FIELD_ATTR_SLUGS = frozenset({'sku-attr', 'size-ab', 'length', 'cover'})

_GROUP_FALLBACK = {
    'zagalne': ('Загальне', 1),
    'rozmiry': ('Розміри', 2),
    'material': ('Матеріал', 3),
}


def product_spec_groups(product):
    from pages.i18n_lib import tr

    groups_by_slug = {g.slug: g for g in AttributeGroup.objects.all()}
    rows_by_group = {}

    def bucket(slug, fallback_title, fallback_order):
        group = groups_by_slug.get(slug)
        if group:
            key = group.pk
            title = group.display_name()
            order = group.sort_order
        else:
            key = f'v:{slug}'
            title = tr(fallback_title)
            order = fallback_order
        return rows_by_group.setdefault(
            key, {'title': title, 'order': order, 'rows': []}
        )

    for slug, label, spec, value, row_order in _product_field_rows(product):
        title, grp_order = _GROUP_FALLBACK[slug]
        bucket(slug, title, grp_order)['rows'].append(
            {
                'k': tr(label),
                'v': tr(value),
                'order': row_order,
                'spec': spec,
            }
        )

    for av in product.attributes.all():
        attr = av.attribute
        if attr.slug in PRODUCT_FIELD_ATTR_SLUGS:
            continue
        group = attr.group
        if group:
            key = group.pk
            title = group.display_name()
            grp_order = group.sort_order
        else:
            key = 0
            title = tr('Інше')
            grp_order = 999
        bucket_rows = rows_by_group.setdefault(
            key, {'title': title, 'order': grp_order, 'rows': []}
        )
        bucket_rows['rows'].append(
            {
                'k': attr.display_name(),
                'v': av.display_value(),
                'order': 100 + attr.sort_order,
                'spec': '',
            }
        )

    groups = sorted(rows_by_group.values(), key=lambda g: g['order'])
    for g in groups:
        g['rows'] = sorted(g['rows'], key=lambda r: r['order'])
        for i, row in enumerate(g['rows']):
            row['zebra'] = i % 2 == 1
    return groups


def _product_field_rows(product):
    sku = (product.sku or '').strip()
    if sku:
        yield 'zagalne', 'Артикул', 'sku', sku, 0
    if product.size_mm:
        yield 'rozmiry', 'Загальна довжина', 'len', f'{product.size_mm} мм', 0
    if product.size_label:
        yield 'rozmiry', 'Розмір A×B', 'ab', f'{product.size_label} мм', 1
    cover = (product.cover or '').strip()
    if cover:
        yield 'material', 'Покриття', 'cover', cover, 1
