"""Характеристики на сторінці товару — плоский список, як у макеті.

Системні рядки (Бренд, Категорія, Артикул, Гарантія, розміри, покриття)
беруться з полів товару. Решта — з характеристик товару (Attribute →
AttributeValue). Назви груп на сайт не виводяться: група лишається лише
необовʼязковою позначкою в адмінці.
"""

from .product_meta import plural_months

# Атрибути, які дублюють поля товару — показуємо лише системний рядок.
PRODUCT_FIELD_ATTR_SLUGS = frozenset({'sku-attr', 'size-ab', 'length', 'cover', 'brand'})

# Порядок як у макеті (Центр замків.dc.html → P.specs):
# Бренд, Країна виробництва, Категорія, Тип механізму, Розмір / модель,
# Колір/покриття, Артикул, Гарантія. Далі — решта за sort_order.
MOCKUP_ORDER = (
    'sys:brand',
    'country',
    'sys:category',
    'mech',
    'model',
    'sys:len',
    'sys:ab',
    'color',
    'sys:cover',
    'sys:sku',
    'sys:warranty',
)
_RANK = {key: i for i, key in enumerate(MOCKUP_ORDER)}
_REST = len(MOCKUP_ORDER)


def _category_label(category):
    from django.utils.translation import get_language

    if category is None:
        return ''
    lang = get_language() or 'ua'
    name = category.card_name(lang)
    parent = category.parent
    if parent is not None:
        return f'{parent.card_name(lang)} / {name}'
    return name


def _brand_value(product, attr_values):
    for av in attr_values:
        if av.attribute.slug == 'brand':
            return (av.display_value() or '').strip()
    return (product.brand or '').strip()


def product_brand(product):
    """Бренд із характеристики slug=brand, інакше зі старого поля товару."""
    return _brand_value(product, product.attributes.all())


def product_spec_rows(product):
    """Плоский список {'k', 'v', 'spec'} у порядку макета."""
    from pages.i18n_lib import tr
    from django.utils.translation import get_language
    from pages.cms_content import get_block_text

    lang = get_language() or 'ua'

    def sys_label(name, fallback):
        return (get_block_text('product', f'spec_{name}_label', lang=lang) or '').strip() or tr(fallback)

    def sys_on(name):
        return (get_block_text('product', f'spec_{name}_visible', lang='ua') or '1').strip() != '0'

    attr_values = list(product.attributes.all())
    rows = []

    def add(key, label, value, spec='', order=(0, 0)):
        value = (value or '').strip() if isinstance(value, str) else value
        if not value:
            return
        rank = _RANK.get(key, _REST)
        rows.append(
            {'k': label, 'v': value, 'spec': spec, '_rank': (rank, order, label)}
        )

    if sys_on('brand'): add('sys:brand', sys_label('brand', 'Бренд'), _brand_value(product, attr_values))
    if sys_on('category'): add('sys:category', sys_label('category', 'Категорія'), _category_label(product.category))
    if product.size_mm and sys_on('len'):
        add('sys:len', sys_label('len', 'Загальна довжина'), f'{product.size_mm} {tr("мм")}', 'len')
    if product.size_label and sys_on('ab'):
        add('sys:ab', sys_label('ab', 'Розмір A×B'), f'{product.size_label} {tr("мм")}', 'ab')
    cover = (product.cover or '').strip()
    if sys_on('sku'): add('sys:sku', sys_label('sku', 'Артикул'), (product.sku or '').strip(), 'sku')
    months = int(product.warranty_months or 0)
    if months > 0 and sys_on('warranty'):
        add('sys:warranty', sys_label('warranty', 'Гарантія'), f'{months} {plural_months(months)}')

    seen_values = set()
    for av in attr_values:
        attr = av.attribute
        if attr.slug in PRODUCT_FIELD_ATTR_SLUGS:
            continue
        value = av.display_value()
        if attr.slug == 'color':
            seen_values.add(value.strip().lower())
        grp = attr.group.sort_order if attr.group_id and attr.group else 999
        add(attr.slug, attr.display_name(), value, order=(grp, attr.sort_order))

    # Покриття з поля товару, якщо воно не повторює «Колір/покриття».
    if cover and cover.lower() not in seen_values and sys_on('cover'):
        add('sys:cover', sys_label('cover', 'Покриття'), tr(cover), 'cover')

    rows.sort(key=lambda r: r['_rank'])
    for r in rows:
        r.pop('_rank', None)
    return rows

