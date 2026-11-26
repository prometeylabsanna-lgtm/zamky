from decimal import Decimal

from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from catalog.models import Attribute, AttributeValue, Category, Product, ProductAttribute
from catalog.templatetags.catalog_tags import chip_remove_query
from catalog.views import PAGE_SIZE


class CatalogPaginationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name='Циліндри', slug='cylinders-page')
        brand = Attribute.objects.create(name='Бренд', slug='brand')
        self.av_abaro = AttributeValue.objects.create(
            attribute=brand, value='ABARO', slug='abaro'
        )
        self.products = []
        for i in range(PAGE_SIZE + 1):
            product = Product.objects.create(
                category=self.cat,
                name=f'Замок {i}',
                slug=f'lock-page-{i}',
                sku=f'PAGE-{i:03d}',
                price=Decimal('100') + i,
                stock=4,
                brand='ABARO' if i == 0 else 'Other',
            )
            self.products.append(product)
        ProductAttribute.objects.create(
            product=self.products[0], attribute_value=self.av_abaro
        )
        self.listing_url = reverse('catalog:category', args=[self.cat.slug])

    def test_invalid_page_returns_200(self):
        response = self.client.get(self.listing_url, {'page': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].number >= 1)

    def test_page_beyond_last_returns_200(self):
        response = self.client.get(self.listing_url, {'page': '999'})
        self.assertEqual(response.status_code, 200)
        page = response.context['page_obj']
        self.assertEqual(page.number, page.paginator.num_pages)

    def test_chip_remove_drops_page(self):
        request = RequestFactory().get(
            self.listing_url,
            {'brand': 'abaro', 'page': '5', 'sort': 'cheap'},
        )
        qs = chip_remove_query({'request': request}, 'brand', 'abaro')
        self.assertNotIn('page=', qs)
        self.assertIn('sort=cheap', qs)

    def test_chip_link_on_stale_page_has_no_page(self):
        response = self.client.get(
            self.listing_url, {'brand': 'abaro', 'page': '5'}
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertNotIn('page=5', body)
