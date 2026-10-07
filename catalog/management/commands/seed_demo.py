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
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductImage,
)
from orders.models import DeliveryDistrict


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
        Category.objects.all().delete()
        Product.objects.all().delete()
        Attribute.objects.all().delete()

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

        attrs = {
            'brand': Attribute.objects.create(name='Виробник/Бренд', slug='brand', sort_order=1),
            'country': Attribute.objects.create(name='Країна виробництва', slug='country', sort_order=2),
            'color': Attribute.objects.create(name='Колір/покриття', slug='color', sort_order=3),
            'mech': Attribute.objects.create(name='Тип механізму', slug='mech', sort_order=4),
        }
        value_cache = {}

        def av(attr_key, value):
            key = (attr_key, value)
            if key not in value_cache:
                value_cache[key] = AttributeValue.objects.create(
                    attribute=attrs[attr_key],
                    value=value,
                    slug=slugify(value) or value.lower(),
                )
            return value_cache[key]

        brands = [
            {'b': 'ABARO', 'code': 'ABR', 'model': 'B100', 'country': 'Туреччина', 'k': 1},
            {'b': 'Mottura', 'code': 'MOT', 'model': 'Champions', 'country': 'Італія', 'k': 2.6},
            {'b': 'Cisa', 'code': 'CIS', 'model': 'Asix', 'country': 'Італія', 'k': 1.9},
            {'b': 'Kale', 'code': 'KAL', 'model': '164 BNE', 'country': 'Туреччина', 'k': 1.3},
            {'b': 'Apecs', 'code': 'APC', 'model': 'Premier', 'country': 'Китай', 'k': 0.8},
        ]
        colors = [
            {'id': 'G', 'label': 'Латунь', 'finish': 'G латунь полірована', 'img': 'abaro-brass.png', 'add': 0},
            {'id': 'N', 'label': 'Нікель', 'finish': 'N нікель сатин', 'img': 'abaro-nickel.png', 'add': 40},
            {'id': 'B', 'label': 'Чорний', 'finish': 'B чорний матовий', 'img': 'abaro-black.png', 'add': 60},
        ]
        sizes = [
            {'len': 60, 'a': 30, 'b': 30, 'p': 400},
            {'len': 70, 'a': 35, 'b': 35, 'p': 460},
            {'len': 80, 'a': 40, 'b': 40, 'p': 520},
            {'len': 90, 'a': 45, 'b': 45, 'p': 590},
        ]
        mechs = [
            {'id': 'kk', 'label': 'Ключ / ключ', 'short': '5 ключів'},
            {'id': 'kt', 'label': 'Ключ / тумблер', 'short': 'ключ/тумблер'},
            {'id': 'half', 'label': 'Половинчастий', 'short': 'половинчастий'},
        ]

        cylinder_cat = categories['Серцевини (циліндри)']
        brand_cat_map = {
            'Mottura': categories['Mottura'],
            'Cisa': categories['Cisa'],
            'Kale': categories['Kale'],
            'Apecs': categories['Apecs'],
        }

        img_dir = settings.BASE_DIR / 'static' / 'img'
        media_seed = Path(settings.MEDIA_ROOT) / 'products'
        media_seed.mkdir(parents=True, exist_ok=True)

        created = 0
        for bi, B in enumerate(brands):
            for si, S in enumerate(sizes):
                for ci, C in enumerate(colors):
                    n = bi * 12 + si * 3 + ci
                    if (n * 7) % 10 > 6:
                        continue
                    M = mechs[(n + bi) % 3]
                    price = Decimal(str(round(((S['p'] + C['add']) * B['k']) / 10) * 10))
                    old = Decimal(str(round(float(price) * 1.3 / 10) * 10))
                    sku = f"{B['code']}-{B['model'].replace(' ', '')}-{S['len']}-{C['id']}".upper()
                    name = (
                        f"Циліндр {B['b']} {B['model']} {S['len']} "
                        f"({S['a']}*{S['b']}) {C['finish']}, {M['short']}"
                    )
                    stock = 0 if n % 11 == 4 else (2 if n % 7 == 3 else 12 + (n % 5))
                    cat = brand_cat_map.get(B['b'], cylinder_cat)
                    product = Product.objects.create(
                        category=cat,
                        name=name,
                        slug=slugify(sku.lower()),
                        sku=sku,
                        price=price,
                        old_price=old,
                        stock=stock,
                        is_active=True,
                        is_hit=n % 3 == 0,
                        is_new=n % 4 == 1,
                        brand=B['b'],
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
                        ProductAttribute.objects.create(
                            product=product,
                            attribute_value=av(key, val),
                        )

                    src = img_dir / C['img']
                    if not src.exists():
                        src = img_dir / 'product-brass.png'
                    dest_name = f'{sku.lower()}.png'
                    dest = media_seed / dest_name
                    if src.exists():
                        shutil.copyfile(src, dest)
                        with dest.open('rb') as fh:
                            ProductImage.objects.create(
                                product=product,
                                image=File(fh, name=dest_name),
                                alt=name,
                                sort_order=0,
                                is_primary=True,
                            )
                        for ti, thumb in enumerate(
                            ['thumb-1.png', 'thumb-2.png', 'thumb-3.png', 'gallery-1.png'],
                            start=1,
                        ):
                            tsrc = img_dir / thumb
                            if tsrc.exists():
                                tdest = media_seed / f'{sku.lower()}-t{ti}.png'
                                shutil.copyfile(tsrc, tdest)
                                with tdest.open('rb') as fh:
                                    ProductImage.objects.create(
                                        product=product,
                                        image=File(fh, name=tdest.name),
                                        alt=f'{name} фото {ti}',
                                        sort_order=ti,
                                    )
                    created += 1

        # Додаткові замки
        lock_cat = categories['Замки']
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
                if key == 'country' and val == 'Україна':
                    ProductAttribute.objects.create(product=product, attribute_value=av(key, val))
                else:
                    ProductAttribute.objects.create(product=product, attribute_value=av(key, val))
            src = img_dir / 'product-chrome.png'
            if src.exists():
                dest = media_seed / f'{sku.lower()}.png'
                shutil.copyfile(src, dest)
                with dest.open('rb') as fh:
                    ProductImage.objects.create(
                        product=product,
                        image=File(fh, name=dest.name),
                        alt=product.name,
                        is_primary=True,
                    )
            created += 1

        self.stdout.write(f'Products created: {created}')
