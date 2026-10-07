import json
import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalog.models import (
    Attribute,
    AttributeGroup,
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductFamily,
    ProductImage,
)
from orders.models import DeliveryDistrict

ABARO_DESC = (
    "Циліндр ABARO B100 — механізм секретності для врізних замків вхідних і міжкімнатних дверей. "
    "Корпус виготовлений з латуні, підходить для більшості замків з європрофілем.\n\n"
    "Конструкція з п'ятьма ключами в комплекті має захист від бампінгу та висвердлювання. "
    "Ключі з пластиковою головкою зручно розрізняти, а заготовки можна виготовити лише за кодовою карткою.\n\n"
    "Перед покупкою виміряйте відстань від центру отвору під кріпильний гвинт до кожного краю двері — "
    "це розміри A і B. Якщо сумніваєтесь, менеджер допоможе підібрати циліндр під ваші двері."
)

ABARO_STOCK = {
    ('N', 90): 0,
    ('N', 80): 3,
    ('B', 90): 2,
    ('B', 80): 0,
}

COLORS = [
    {
        'id': 'G',
        'label': 'Латунь',
        'finish': 'G латунь полірована',
        'cover': 'Полірована латунь',
        'img': 'abaro-brass.png',
        'add': 0,
    },
    {
        'id': 'N',
        'label': 'Нікель',
        'finish': 'N нікель сатин',
        'cover': 'Матовий нікель',
        'img': 'abaro-nickel.png',
        'add': 40,
    },
    {
        'id': 'B',
        'label': 'Чорний',
        'finish': 'B чорний матовий',
        'cover': 'Чорне матове',
        'img': 'abaro-black.png',
        'add': 60,
    },
]

SIZES = [
    {'len': 60, 'a': 30, 'b': 30, 'p': 400},
    {'len': 70, 'a': 35, 'b': 35, 'p': 460},
    {'len': 80, 'a': 40, 'b': 40, 'p': 520},
    {'len': 90, 'a': 45, 'b': 45, 'p': 590},
]

EXTRA_THUMBS = ['thumb-2.png', 'thumb-3.png', 'thumb-4.png', 'thumb-5.png', 'thumb-6.png']


class Command(BaseCommand):
    help = 'Заповнює демо-дані з дизайну E-com'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding districts...')
        self._seed_districts()
        self.stdout.write('Seeding catalog...')
        self._seed_catalog()
        self.stdout.write(self.style.SUCCESS('Demo data ready.'))

    def _seed_districts(self):
        path = settings.DISTRICTS_JSON
        data = json.loads(path.read_text(encoding='utf-8'))
        for i, d in enumerate(data.get('districts', [])):
            DeliveryDistrict.objects.update_or_create(
                slug=d['slug'],
                defaults={
                    'name': d['name'],
                    'short': d.get('short', d['name']),
                    'name_locative': d.get('name_locative', ''),
                    'delivery_note': d.get('delivery', ''),
                    'areas': d.get('areas', []),
                    'h1': d.get('h1')
                    or f"Замки для дверей — купити в {d.get('name_locative') or d['name']}",
                    'seo_text': d.get('seo_text')
                    or (
                        f"Доставляємо замки та серцевини у {d.get('name_locative') or d['name']}. "
                        f"{d.get('delivery', '')}. Райони: {', '.join(d.get('areas', []))}."
                    ),
                    'is_active': True,
                    'sort_order': i,
                },
            )

    def _seed_catalog(self):
        Product.objects.all().delete()
        ProductFamily.objects.all().delete()
        Category.objects.all().delete()
        Attribute.objects.all().delete()
        AttributeGroup.objects.all().delete()

        cats_data = [
            ('Серцевини (циліндри)', 'cyl', None),
            ('Замки', 'pad', None),
            ('Замки підвищеного захисту', 'shield', None),
            ('Mottura', 'brand', 'mottura.png'),
            ('Cisa', 'brand', 'cisa.png'),
            ('Elbor', 'brand', 'elbor.png'),
            ('Guardian', 'brand', 'guardian.png'),
            ('Apecs', 'brand', 'apecs.png'),
            ('Securame', 'brand', 'securame.png'),
            ('Kale', 'brand', 'kale.png'),
        ]
        categories = {}
        for i, (name, icon, logo) in enumerate(cats_data):
            cat = Category.objects.create(
                name=name,
                slug=slugify(name) or f'cat-{i}',
                icon=icon,
                sort_order=i,
                is_active=True,
            )
            if logo:
                src = settings.BASE_DIR / 'static' / 'img' / logo
                if src.exists():
                    with src.open('rb') as fh:
                        cat.logo.save(logo, File(fh), save=True)
            categories[name] = cat

        groups = {
            'general': AttributeGroup.objects.create(name='Загальне', slug='zagalne', sort_order=1),
            'sizes': AttributeGroup.objects.create(name='Розміри', slug='rozmiry', sort_order=2),
            'material': AttributeGroup.objects.create(name='Матеріал', slug='material', sort_order=3),
            'safety': AttributeGroup.objects.create(
                name='Безпека та комплектація',
                slug='bezpeka-ta-komplektatsiia',
                sort_order=4,
            ),
            'filters': AttributeGroup.objects.create(name='Фільтри', slug='filters', sort_order=10),
        }

        attrs = {
            'brand': Attribute.objects.create(
                name='Бренд', slug='brand', group=groups['general'], filterable=True, sort_order=1
            ),
            'model': Attribute.objects.create(
                name='Модель', slug='model', group=groups['general'], filterable=False, sort_order=2
            ),
            'sku_attr': Attribute.objects.create(
                name='Артикул', slug='sku-attr', group=groups['general'], filterable=False, sort_order=3
            ),
            'mech': Attribute.objects.create(
                name='Тип', slug='mech', group=groups['general'], filterable=True, sort_order=4
            ),
            'len': Attribute.objects.create(
                name='Загальна довжина',
                slug='length',
                group=groups['sizes'],
                filterable=False,
                sort_order=1,
            ),
            'ab': Attribute.objects.create(
                name='Розмір A×B',
                slug='size-ab',
                group=groups['sizes'],
                filterable=False,
                sort_order=2,
            ),
            'body': Attribute.objects.create(
                name='Корпус',
                slug='body',
                group=groups['material'],
                filterable=False,
                sort_order=1,
            ),
            'cover': Attribute.objects.create(
                name='Покриття',
                slug='cover',
                group=groups['material'],
                filterable=False,
                sort_order=2,
            ),
            'bump': Attribute.objects.create(
                name='Захист від бампінгу',
                slug='bump',
                group=groups['safety'],
                filterable=False,
                sort_order=1,
            ),
            'drill': Attribute.objects.create(
                name='Захист від висвердлювання',
                slug='drill',
                group=groups['safety'],
                filterable=False,
                sort_order=2,
            ),
            'keys': Attribute.objects.create(
                name='Кількість ключів',
                slug='keys',
                group=groups['safety'],
                filterable=False,
                sort_order=3,
            ),
            'card': Attribute.objects.create(
                name='Кодова картка',
                slug='code-card',
                group=groups['safety'],
                filterable=False,
                sort_order=4,
            ),
            'country': Attribute.objects.create(
                name='Країна виробництва',
                slug='country',
                group=groups['filters'],
                filterable=True,
                sort_order=1,
            ),
            'color': Attribute.objects.create(
                name='Колір/покриття',
                slug='color',
                group=groups['filters'],
                filterable=True,
                sort_order=2,
            ),
        }
        value_cache = {}

        def av(attr_key, value):
            key = (attr_key, value)
            if key not in value_cache:
                base = slugify(value) or value.lower().replace(' ', '-')
                slug = base
                i = 1
                while AttributeValue.objects.filter(attribute=attrs[attr_key], slug=slug).exists():
                    slug = f'{base}-{i}'
                    i += 1
                value_cache[key] = AttributeValue.objects.create(
                    attribute=attrs[attr_key],
                    value=value,
                    slug=slug,
                )
            return value_cache[key]

        img_dir = settings.BASE_DIR / 'static' / 'img'
        media_seed = Path(settings.MEDIA_ROOT) / 'products'
        media_seed.mkdir(parents=True, exist_ok=True)

        created = 0
        created += self._seed_abaro(
            categories['Серцевини (циліндри)'],
            attrs,
            av,
            img_dir,
            media_seed,
        )
        created += self._seed_other_brands(categories, attrs, av, img_dir, media_seed)
        created += self._seed_locks(categories, attrs, av, img_dir, media_seed)
        self.stdout.write(f'Products created: {created}')

    def _attach_image(self, product, src, dest_name, alt, sort_order, primary=False):
        media_seed = Path(settings.MEDIA_ROOT) / 'products'
        dest = media_seed / dest_name
        if not src.exists():
            return
        shutil.copyfile(src, dest)
        with dest.open('rb') as fh:
            ProductImage.objects.create(
                product=product,
                image=File(fh, name=dest_name),
                alt=alt,
                sort_order=sort_order,
                is_primary=primary,
            )

    def _seed_abaro(self, category, attrs, av, img_dir, media_seed):
        family = ProductFamily.objects.create(
            name='ABARO B100',
            slug='abaro-b100',
            brand='ABARO',
            description=ABARO_DESC,
            short_description='Циліндровий механізм для дверей із комплектом ключів.',
        )
        n = 0
        for C in COLORS:
            for S in SIZES:
                price = Decimal(str(S['p'] + C['add']))
                old = Decimal(str(round(float(price) * 1.3 / 10) * 10))
                sku = f"ABR-B100-{S['len']}-{C['id']}"
                name = (
                    f"Циліндр ABARO B100 {S['len']} "
                    f"({S['a']}*{S['b']}) {C['finish']} 5 ключів"
                )
                stock = ABARO_STOCK.get((C['id'], S['len']), 20)
                product = Product.objects.create(
                    category=category,
                    family=family,
                    name=name,
                    slug=slugify(sku.lower()),
                    sku=sku,
                    price=price,
                    old_price=old,
                    stock=stock,
                    is_active=True,
                    is_hit=S['len'] == 60 and C['id'] == 'G',
                    is_new=False,
                    brand='ABARO',
                    color_code=C['id'],
                    color_label=C['label'],
                    finish=C['finish'],
                    cover=C['cover'],
                    size_mm=S['len'],
                    size_a=S['a'],
                    size_b=S['b'],
                    short_description=family.short_description,
                    description=family.description,
                )
                for key, val in (
                    ('brand', 'ABARO'),
                    ('model', 'B100'),
                    ('sku_attr', sku),
                    ('mech', 'Ключ / ключ'),
                    ('len', f"{S['len']} мм"),
                    ('ab', f"{S['a']}×{S['b']} мм"),
                    ('body', 'Латунь'),
                    ('cover', C['cover']),
                    ('bump', 'Так'),
                    ('drill', 'Так'),
                    ('keys', '5'),
                    ('card', 'Так'),
                    ('country', 'Туреччина'),
                    ('color', C['label']),
                ):
                    ProductAttribute.objects.create(product=product, attribute_value=av(key, val))

                primary = img_dir / C['img']
                self._attach_image(
                    product,
                    primary,
                    f'{sku.lower()}.png',
                    name,
                    0,
                    primary=True,
                )
                for ti, thumb in enumerate(EXTRA_THUMBS, start=1):
                    self._attach_image(
                        product,
                        img_dir / thumb,
                        f'{sku.lower()}-t{ti}.png',
                        f'{name} — фото {ti + 1}',
                        ti,
                    )
                n += 1
        return n

    def _seed_other_brands(self, categories, attrs, av, img_dir, media_seed):
        brands = [
            {'b': 'Mottura', 'code': 'MOT', 'model': 'Champions', 'country': 'Італія', 'k': 2.6},
            {'b': 'Cisa', 'code': 'CIS', 'model': 'Asix', 'country': 'Італія', 'k': 1.9},
            {'b': 'Kale', 'code': 'KAL', 'model': '164 BNE', 'country': 'Туреччина', 'k': 1.3},
            {'b': 'Apecs', 'code': 'APC', 'model': 'Premier', 'country': 'Китай', 'k': 0.8},
        ]
        mechs = [
            {'id': 'kk', 'label': 'Ключ / ключ', 'short': '5 ключів'},
            {'id': 'kt', 'label': 'Ключ / тумблер', 'short': 'ключ/тумблер'},
            {'id': 'half', 'label': 'Половинчастий', 'short': 'половинчастий'},
        ]
        brand_cat_map = {
            'Mottura': categories['Mottura'],
            'Cisa': categories['Cisa'],
            'Kale': categories['Kale'],
            'Apecs': categories['Apecs'],
        }
        cylinder_cat = categories['Серцевини (циліндри)']
        n = 0
        for bi, B in enumerate(brands):
            for si, S in enumerate(SIZES):
                for ci, C in enumerate(COLORS):
                    idx = bi * 12 + si * 3 + ci
                    if (idx * 7) % 10 > 6:
                        continue
                    M = mechs[(idx + bi) % 3]
                    price = Decimal(str(round(((S['p'] + C['add']) * B['k']) / 10) * 10))
                    old = Decimal(str(round(float(price) * 1.3 / 10) * 10))
                    sku = f"{B['code']}-{B['model'].replace(' ', '')}-{S['len']}-{C['id']}".upper()
                    name = (
                        f"Циліндр {B['b']} {B['model']} {S['len']} "
                        f"({S['a']}*{S['b']}) {C['finish']}, {M['short']}"
                    )
                    stock = 0 if idx % 11 == 4 else (2 if idx % 7 == 3 else 12 + (idx % 5))
                    product = Product.objects.create(
                        category=brand_cat_map.get(B['b'], cylinder_cat),
                        name=name,
                        slug=slugify(sku.lower()),
                        sku=sku,
                        price=price,
                        old_price=old,
                        stock=stock,
                        is_active=True,
                        is_hit=idx % 3 == 0,
                        is_new=idx % 4 == 1,
                        brand=B['b'],
                        color_code=C['id'],
                        color_label=C['label'],
                        finish=C['finish'],
                        cover=C['cover'],
                        size_mm=S['len'],
                        size_a=S['a'],
                        size_b=S['b'],
                        short_description='Циліндровий механізм для дверей із комплектом ключів.',
                        description=(
                            'Надійна серцевина для міжкімнатних і вхідних дверей. '
                            'Сумісна з більшістю європейських замків. Гарантія 12 місяців.'
                        ),
                    )
                    for key, val in (
                        ('brand', B['b']),
                        ('country', B['country']),
                        ('color', C['label']),
                        ('mech', M['label']),
                    ):
                        ProductAttribute.objects.create(product=product, attribute_value=av(key, val))
                    src = img_dir / C['img']
                    if not src.exists():
                        src = img_dir / 'product-brass.png'
                    self._attach_image(product, src, f'{sku.lower()}.png', name, 0, primary=True)
                    for ti, thumb in enumerate(['thumb-1.png', 'thumb-2.png', 'thumb-3.png'], start=1):
                        self._attach_image(
                            product,
                            img_dir / thumb,
                            f'{sku.lower()}-t{ti}.png',
                            f'{name} фото {ti}',
                            ti,
                        )
                    n += 1
        return n

    def _seed_locks(self, categories, attrs, av, img_dir, media_seed):
        lock_cat = categories['Замки']
        n = 0
        for i, brand in enumerate(['Elbor', 'Guardian', 'Securame']):
            sku = f'LCK-{brand[:3].upper()}-{100 + i}'
            product = Product.objects.create(
                category=categories.get(brand, lock_cat),
                name=f'Замок врізний {brand} Secure {100 + i}',
                slug=slugify(sku.lower()),
                sku=sku,
                price=Decimal(str(1200 + i * 250)),
                old_price=Decimal(str(1500 + i * 250)),
                stock=8,
                is_active=True,
                is_hit=True,
                is_new=i == 0,
                brand=brand,
                short_description='Врізний замок підвищеної надійності.',
                description='Металевий корпус, комплект кріплення, ключі в наборі.',
            )
            for key, val in (
                ('brand', brand),
                ('country', 'Україна' if brand == 'Elbor' else 'Італія'),
                ('color', 'Нікель'),
                ('mech', 'Ключ / ключ'),
            ):
                ProductAttribute.objects.create(product=product, attribute_value=av(key, val))
            src = img_dir / 'product-chrome.png'
            self._attach_image(product, src, f'{sku.lower()}.png', product.name, 0, primary=True)
            n += 1
        return n
