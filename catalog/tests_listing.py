from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from catalog.category_tree import ensure_category_tree
from catalog.listing_scope import listing_scope
from catalog.models import Category, Product


class ListingScopeTests(TestCase):
    def setUp(self):
        ensure_category_tree()
        self.cyl = Category.objects.get(name='Циліндри', parent__isnull=True)
        self.mottura = Category.objects.get(name='Mottura', parent__isnull=True)
        leaf = Category.objects.get(name='Стандартні', parent__name='Ключ-ключ')
        Product.objects.create(
            category=leaf,
            name='Циліндр Apecs AP-1',
            slug='mk-apecs-1',
            sku='TST-AP-1',
            price=Decimal('3620'),
            catalog_order=1,
            brand='Apecs',
        )
        Product.objects.create(
            category=leaf,
            name='Циліндр Mottura MO-1',
            slug='mk-mot-1',
            sku='TST-MO-1',
            price=Decimal('2320'),
            catalog_order=2,
            brand='Mottura',
        )

    def test_type_listing_keeps_all_brands(self):
        page = self.client.get(
            reverse('catalog:category', args=[self.cyl.slug]), follow=True
        )
        skus = [p.sku for p in page.context['products']]
        self.assertIn('TST-AP-1', skus)
        self.assertIn('TST-MO-1', skus)
        chips = [c['name'] for c in page.context['category_chips']]
        self.assertIn('Ключ-ключ', chips)

    def test_brand_listing_filters_by_brand_not_tree(self):
        scope = listing_scope(self.mottura)
        self.assertEqual(scope['brand'], 'Mottura')
        page = self.client.get(
            reverse('catalog:category', args=[self.mottura.slug]), follow=True
        )
        skus = [p.sku for p in page.context['products']]
        self.assertIn('TST-MO-1', skus)
        self.assertNotIn('TST-AP-1', skus)
        self.assertTrue(all(p.brand == 'Mottura' for p in page.context['products']))
