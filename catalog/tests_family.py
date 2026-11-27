from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import NoReverseMatch, reverse

from catalog.models import Category, Product, ProductImage
from catalog.product_variants import build_variant_context

_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
    b'\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx'
    b'\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND'
    b'\xaeB`\x82'
)


def _png(name='swatch.png'):
    return SimpleUploadedFile(name, _PNG, content_type='image/png')


class OwnVariantTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Циліндри', slug='cyl-own')
        self.product = Product.objects.create(
            category=self.cat,
            name='Циліндр латунь',
            slug='own-g',
            sku='OWN-G',
            price=Decimal('100'),
            color_code='G',
            size_mm=60,
            size_a=30,
            size_b=30,
        )
        Product.objects.create(
            category=self.cat,
            name='Циліндр нікель',
            slug='own-n',
            sku='OWN-N',
            price=Decimal('110'),
            color_code='N',
            size_mm=70,
            size_a=35,
            size_b=35,
        )

    def test_own_color_and_size_only(self):
        variants, colors, sizes = build_variant_context(self.product)
        self.assertEqual(len(variants), 1)
        self.assertEqual(len(colors), 1)
        self.assertEqual(colors[0]['code'], 'G')
        self.assertEqual(len(sizes), 1)
        self.assertEqual(sizes[0]['len'], 60)

    def test_swatch_from_product_photo(self):
        ProductImage.objects.create(product=self.product, image=_png('prod.png'))
        _variants, colors, _sizes = build_variant_context(self.product)
        self.assertTrue(colors[0]['img'])

    def test_pdp_has_no_family_label(self):
        page = self.client.get(
            reverse('catalog:product', args=[self.product.slug]), follow=True
        )
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'Сімʼя')
        self.assertNotContains(page, 'Плашка кольору')
        self.assertContains(page, 'Колір серцевини')


class FamilyAdminGoneTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            'fadmin', 'f@example.com', 'pass12345'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.cat = Category.objects.create(name='Циліндри', slug='cyl-fam-admin')
        self.product = Product.objects.create(
            category=self.cat,
            name='Варіант 70 чорний',
            slug='var-70-b',
            sku='VAR-70-B',
            price=Decimal('200'),
            color_code='B',
            size_mm=70,
        )

    def test_family_admin_removed(self):
        with self.assertRaises(NoReverseMatch):
            reverse('admin:catalog_productfamily_changelist')

    def test_product_admin_has_no_family_field(self):
        page = self.client.get(
            reverse('admin:catalog_product_change', args=[self.product.pk])
        )
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'id="id_family"')
