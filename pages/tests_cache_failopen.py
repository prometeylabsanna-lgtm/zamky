from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from catalog.models import Category, Product, Review


@override_settings(ALLOWED_HOSTS=['*'])
class CacheFailOpenTests(TestCase):
    def tearDown(self):
        translation.deactivate_all()

    @patch('config.cache_safe.cache.get', side_effect=RuntimeError('missing cache table'))
    @patch('config.cache_safe.cache.set', side_effect=RuntimeError('missing cache table'))
    def test_home_ok_when_cache_backend_down(self, _set, _get):
        with translation.override('ua'):
            response = self.client.get(reverse('catalog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Каталог товарів')

    @patch('config.cache_safe.cache.add', side_effect=RuntimeError('missing cache table'))
    @patch('config.cache_safe.cache.incr', side_effect=RuntimeError('missing cache table'))
    def test_review_saved_when_cache_backend_down(self, _incr, _add):
        cat = Category.objects.create(name='Кеш', slug='cache-failopen')
        product = Product.objects.create(
            category=cat,
            name='Замок',
            slug='cache-failopen-lock',
            sku='CACHE-FO-1',
            price=Decimal('100'),
            is_active=True,
        )
        url = reverse('catalog:product_review', args=[product.slug])
        response = self.client.post(
            url,
            {
                'author_name': 'Оля',
                'rating': '5',
                'text': 'Замок стоїть уже місяць',
            },
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'після модерації')
        self.assertEqual(Review.objects.count(), 1)
