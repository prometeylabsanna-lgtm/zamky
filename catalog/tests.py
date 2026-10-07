from decimal import Decimal

from django.core.management import call_command
from django.db.models import Max
from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Attribute, AttributeValue, Category, Product, ProductAttribute
from catalog.views import plural_goods


class CatalogFilterTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name='Циліндри', slug='cylinders')
        brand = Attribute.objects.create(name='Бренд', slug='brand')
        color = Attribute.objects.create(name='Колір', slug='color')
        self.av_abaro = AttributeValue.objects.create(attribute=brand, value='ABARO', slug='abaro')
        self.av_brass = AttributeValue.objects.create(attribute=color, value='Латунь', slug='latun')
        self.p1 = Product.objects.create(
            category=self.cat,
            name='ABARO Brass',
            slug='abaro-brass',
            sku='ABR-1',
            price=Decimal('400'),
            stock=10,
            brand='ABARO',
        )
        self.p2 = Product.objects.create(
            category=self.cat,
            name='Mottura Nickel',
            slug='mottura-nickel',
            sku='MOT-1',
            price=Decimal('1200'),
            stock=10,
            brand='Mottura',
        )
        ProductAttribute.objects.create(product=self.p1, attribute_value=self.av_abaro)
        ProductAttribute.objects.create(product=self.p1, attribute_value=self.av_brass)

    def test_pages_ok(self):
        for name, args in [
            ('catalog:home', []),
            ('catalog:catalog', []),
            ('catalog:product', [self.p1.slug]),
            ('pages:info', []),
            ('orders:checkout', []),
        ]:
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 200, name)

    def test_brand_filter(self):
        url = reverse('catalog:catalog')
        response = self.client.get(url, {'brand': 'abaro'})
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].sku, 'ABR-1')

    def test_price_filter(self):
        url = reverse('catalog:catalog')
        response = self.client.get(url, {'price_min': 1000, 'price_max': 2000})
        products = list(response.context['products'])
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].sku, 'MOT-1')

    def test_sort_cheap(self):
        url = reverse('catalog:catalog')
        response = self.client.get(url, {'sort': 'cheap'})
        products = list(response.context['products'])
        self.assertEqual(products[0].sku, 'ABR-1')

    def test_sku_filter(self):
        response = self.client.get(reverse('catalog:catalog'), {'sku': 'MOT'})
        products = list(response.context['products'])
        self.assertEqual(len(products), 1)


class PluralGoodsTests(TestCase):
    def test_plural_42_towary(self):
        from django.utils import translation

        with translation.override('ua'):
            self.assertEqual(plural_goods(1), 'товар')
            self.assertEqual(plural_goods(2), 'товари')
            self.assertEqual(plural_goods(42), 'товари')
            self.assertEqual(plural_goods(5), 'товарів')
            self.assertEqual(plural_goods(11), 'товарів')


class SeedDemoTests(TestCase):
    def _catalog_qs(self):
        return Product.objects.filter(is_active=True, catalog_order__lt=500).exclude(
            sku__startswith='HOME-'
        )

    def test_seed_demo_42_max_1690_idempotent(self):
        call_command('seed_demo')
        qs = self._catalog_qs()
        self.assertEqual(qs.count(), 42)
        self.assertEqual(qs.aggregate(hi=Max('price'))['hi'], Decimal('1690.00'))

        call_command('seed_demo')
        qs2 = self._catalog_qs()
        self.assertEqual(qs2.count(), 42)
        self.assertEqual(qs2.aggregate(hi=Max('price'))['hi'], Decimal('1690.00'))
        self.assertEqual(
            Product.objects.filter(sku__startswith='HOME-HIT-').count(),
            8,
        )
        self.assertEqual(
            Product.objects.filter(sku__startswith='HOME-NEW-').count(),
            8,
        )

        from django.utils import translation

        with translation.override('ua'):
            response = self.client.get(reverse('catalog:catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['count_label'], '42 товари')
        self.assertEqual(response.context['price_hi'], 1690)
