from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Category, Product
from catalog.search import filter_queryset_by_query, score_product


class SearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name='Серцевини (циліндри)', slug='cylinders')
        self.p = Product.objects.create(
            category=self.cat,
            name='Циліндр ABARO B100 60',
            slug='abaro-cyl',
            sku='ABR-B100-60-G',
            price=Decimal('400'),
            stock=5,
            brand='ABARO',
            catalog_order=1,
        )

    def test_cyrillic_exact_and_prefix_score(self):
        self.assertGreaterEqual(score_product(self.p, 'циліндр'), 70)
        self.assertGreaterEqual(score_product(self.p, 'цил'), 50)
        self.assertGreaterEqual(score_product(self.p, 'ABARO'), 70)

    def test_typo_tolerance(self):
        # одна зайва літера / близьке написання
        self.assertGreaterEqual(score_product(self.p, 'циліндрр'), 35)
        self.assertGreaterEqual(score_product(self.p, 'цилінд'), 50)

    def test_catalog_q_returns_products(self):
        url = reverse('catalog:catalog')
        for q in ('циліндр', 'цил', 'abaro', 'ABR'):
            response = self.client.get(url, {'q': q})
            self.assertEqual(response.status_code, 200, q)
            products = list(response.context['products'])
            self.assertGreaterEqual(len(products), 1, q)

    def test_suggest_api(self):
        url = reverse('catalog:api_search')
        response = self.client.get(url, {'q': 'цил'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['items'])
        labels = ' '.join(item['label'].casefold() for item in data['items'])
        self.assertTrue('цилінд' in labels or 'abaro' in labels)

    def test_filter_queryset_order(self):
        other_cat = Category.objects.create(name='Накладні замки', slug='rim-locks')
        other = Product.objects.create(
            category=other_cat,
            name='Замок накладний',
            slug='rim-lock',
            sku='LOCK-1',
            price=Decimal('900'),
            stock=2,
            brand='Kale',
            catalog_order=2,
        )
        qs = filter_queryset_by_query(Product.objects.all(), 'циліндр')
        ids = list(qs.values_list('pk', flat=True))
        self.assertIn(self.p.pk, ids)
        self.assertNotIn(other.pk, ids)
        self.assertEqual(ids[0], self.p.pk)
