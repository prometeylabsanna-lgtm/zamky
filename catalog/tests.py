from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Attribute, AttributeValue, Category, Product, ProductAttribute


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
