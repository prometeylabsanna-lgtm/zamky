"""Вітрина з макета Центр замків.dc.html: 6 типів × 14 товарів."""

from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.utils.text import slugify

from catalog.category_tree import MENU_TREE, TYPE_ROOT_NAMES, ensure_category_tree

MOCKUP_BRANDS = ('Mottura', 'Cisa', 'Elbor', 'Apecs', 'Securame', 'Kale')
MOCKUP_COUNTRY = {
    'Mottura': 'Італія',
    'Cisa': 'Італія',
    'Elbor': 'Україна',
    'Apecs': 'Україна',
    'Securame': 'Італія',
    'Kale': 'Туреччина',
}
MOCKUP_COLORS = ('Нікель', 'Латунь', 'Хром', 'Чорний')
MOCKUP_ROOTS = (
    {
        'type': 'Замок врізний',
        'img': 'menu/p2_8.png',
        'mech': ('Циліндровий', 'Сувальдний', 'Електромеханічний'),
        'size': ('55 мм', '60 мм', '85 мм'),
    },
    {
        'type': 'Циліндр',
        'img': 'menu/p2_9.png',
        'mech': ('Ключ-ключ', 'Ключ-вертушка'),
        'size': ('60 (30*30)', '70 (35*35)', '80 (40*40)'),
    },
    {
        'type': 'Ручка дверна',
        'img': 'menu/p2_10.png',
        'mech': ('На розетці', 'На планці'),
        'size': ('квадратна розетка', 'кругла розетка'),
    },
    {
        'type': 'Броненакладка',
        'img': 'menu/p2_11.png',
        'mech': ('Накладна', 'Врізна'),
        'size': ('клас 2', 'клас 3', 'клас 4'),
    },
    {
        'type': 'Дотягувач',
        'img': 'menu/p2_12.png',
        'mech': ('Важільний', 'Ковзний'),
        'size': ('EN 2-4', 'EN 3', 'EN 2-5'),
    },
    {
        'type': 'Кодовий замок',
        'img': 'menu/p2_28.png',
        'mech': ('Кодовий', 'Біометричний', 'RFID'),
        'size': ('YB-300', 'YB-500', 'YB-700'),
    },
)
LEGACY_SKU_PREFIXES = ('ABR-', 'MOT-', 'CIS-', 'KAL-', 'APC-', 'LCK-')


def mockup_specs():
    rows = []
    for r in range(6):
        root = MOCKUP_ROOTS[r]
        tree = list(MENU_TREE[r]['tree'].items())
        for k in range(14):
            brand = MOCKUP_BRANDS[(k * 5 + r) % 6]
            sub_name, leaves = tree[k % len(tree)]
            leaf = None
            if leaves:
                leaf = leaves[(k // len(tree)) % len(leaves)]
            price = round((300 + ((k * 733 + r * 1291) % 5300)) / 10) * 10
            color = MOCKUP_COLORS[(k + r) % 4]
            size = root['size'][k % len(root['size'])]
            code = f'{brand[:2].upper()}-{100 + ((k * 37 + r * 11) % 900)}'
            rows.append(
                {
                    'r': r,
                    'k': k,
                    'type_name': TYPE_ROOT_NAMES[r],
                    'sub_name': sub_name,
                    'leaf_name': leaf,
                    'brand': brand,
                    'country': MOCKUP_COUNTRY[brand],
                    'color': color,
                    'mech': root['mech'][k % len(root['mech'])],
                    'size': size,
                    'price': price,
                    'old': round(price * 1.3 / 10) * 10 if k % 3 == 0 else None,
                    'stock': 0 if k % 6 == 5 else 12,
                    'rating': 3 + ((k + r) % 3),
                    'pop': (k * 17 + r * 5) % 29,
                    'is_new': k % 4 == 1,
                    'img': root['img'],
                    'sku': str(10000 + r * 1000 + k * 37),
                    'name': (
                        f'{root["type"]} {brand} {code} {size}, {color.lower()}'
                    ),
                }
            )
    return rows


def mockup_sku_set():
    return {row['sku'] for row in mockup_specs()}


def _parse_size(size):
    text = size.replace('*', '×').replace('x', '×')
    mm = None
    a = b = None
    if text[:2].isdigit():
        mm = int(''.join(ch for ch in text[:3] if ch.isdigit()) or 0) or None
    if '×' in text:
        left, right = text.split('×', 1)
        digits_a = ''.join(ch for ch in left if ch.isdigit())
        digits_b = ''.join(ch for ch in right if ch.isdigit())
        if digits_a:
            a = int(digits_a[-2:] if len(digits_a) > 2 else digits_a)
        if digits_b:
            b = int(digits_b[:2])
    return mm, a, b


def _type_leaf(spec):
    from catalog.models import Category

    root = Category.objects.filter(
        name=spec['type_name'], parent__isnull=True, is_active=True
    ).first()
    if root is None:
        return None
    sub = Category.objects.filter(parent=root, name=spec['sub_name']).first()
    if sub is None:
        return root
    if spec['leaf_name']:
        leaf = Category.objects.filter(parent=sub, name=spec['leaf_name']).first()
        return leaf or sub
    return sub


def _attr_value(cache, slug, value):
    from catalog.models import Attribute, AttributeValue

    key = (slug, value)
    if key in cache:
        return cache[key]
    attr = Attribute.objects.filter(slug=slug).first()
    if attr is None:
        cache[key] = None
        return None
    av = AttributeValue.objects.filter(attribute=attr, value=value).first()
    if av is None:
        base = slugify(value) or value.lower().replace(' ', '-')
        slug_val = base
        n = 1
        while AttributeValue.objects.filter(attribute=attr, slug=slug_val).exists():
            slug_val = f'{base}-{n}'
            n += 1
        av = AttributeValue.objects.create(attribute=attr, value=value, slug=slug_val)
    cache[key] = av
    return av


def _attach_img(product, rel_path):
    src = Path(settings.BASE_DIR) / 'static' / 'img' / rel_path
    if not src.exists():
        return
    from catalog.models import ProductImage

    if product.images.exists():
        return
    dest_name = f'{product.sku.lower()}-{src.name}'
    with src.open('rb') as fh:
        ProductImage.objects.create(
            product=product,
            image=File(fh, name=dest_name),
            alt=product.name,
            sort_order=1,
            is_primary=True,
        )


def park_legacy_vitrine():
    from catalog.db_compat import product_qs

    keep = mockup_sku_set()
    parked = 0
    qs = product_qs().filter(catalog_order__lt=500).exclude(sku__startswith='HOME-')
    for product in qs:
        if product.sku in keep:
            continue
        if product.sku.startswith(LEGACY_SKU_PREFIXES) or product.brand == 'ABARO':
            product.catalog_order = 500 + int(product.catalog_order or 0)
            product.save(update_fields=['catalog_order'])
            parked += 1
    return parked


def _rename_filter_titles():
    from catalog.models import Attribute

    Attribute.objects.filter(slug='brand', name='Бренд').update(name='Виробник/Бренд')
    Attribute.objects.filter(slug='mech', name='Тип').update(name='Тип механізму')


def sync_mockup_products():
    from catalog.db_compat import missing_product_columns, product_qs
    from catalog.models import Product, ProductAttribute

    if missing_product_columns():
        return

    ensure_category_tree()
    _rename_filter_titles()
    cache = {}
    created = 0
    for spec in mockup_specs():
        leaf = _type_leaf(spec)
        mm, a, b = _parse_size(spec['size'])
        defaults = {
            'category': leaf,
            'name': spec['name'],
            'price': Decimal(str(spec['price'])),
            'old_price': Decimal(str(spec['old'])) if spec['old'] else None,
            'stock': spec['stock'],
            'is_active': True,
            'is_new': spec['is_new'],
            'catalog_order': spec['pop'] + spec['r'] * 30,
            'rating': spec['rating'],
            'brand': spec['brand'],
            'color_label': spec['color'],
            'size_mm': mm,
            'size_a': a,
            'size_b': b,
            'short_description': f'{spec["type_name"]} {spec["brand"]}.',
        }
        product = product_qs().filter(sku=spec['sku']).first()
        if product is None:
            product = Product.objects.create(
                sku=spec['sku'],
                slug=slugify(f'mk-{spec["sku"]}-{spec["name"]}')[:300],
                **defaults,
            )
            created += 1
        else:
            for field, value in defaults.items():
                setattr(product, field, value)
            product.save()
        pairs = (
            ('brand', spec['brand']),
            ('country', spec['country']),
            ('color', spec['color']),
            ('mech', spec['mech']),
        )
        for slug, value in pairs:
            av = _attr_value(cache, slug, value)
            if av is None:
                continue
            ProductAttribute.objects.get_or_create(product=product, attribute_value=av)
        _attach_img(product, spec['img'])
    park_legacy_vitrine()
    return created
