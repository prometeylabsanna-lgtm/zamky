from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import (
    Category,
    FamilyColorSwatch,
    Product,
    ProductFamily,
    ProductImage,
)
from catalog.product_variants import build_variant_context

_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
    b'\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx'
    b'\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND'
    b'\xaeB`\x82'
)


def _png(name='swatch.png'):
    return SimpleUploadedFile(name, _PNG, content_type='image/png')


class FamilySwatchTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Циліндри', slug='cyl-fam')
        self.family = ProductFamily.objects.create(name='ABARO B100', slug='abaro-fam')
        self.p_g = Product.objects.create(
            category=self.cat,
            family=self.family,
            name='Циліндр латунь',
            slug='fam-g',
            sku='FAM-G',
            price=Decimal('100'),
            color_code='G',
            size_mm=60,
            size_a=30,
            size_b=30,
        )
        self.p_n = Product.objects.create(
            category=self.cat,
            family=self.family,
            name='Циліндр нікель',
            slug='fam-n',
            sku='FAM-N',
            price=Decimal('110'),
            color_code='N',
            size_mm=60,
            size_a=30,
            size_b=30,
        )

    def test_solo_uses_product_photo(self):
        solo = Product.objects.create(
            category=self.cat,
            name='тест',
            slug='solo-tone',
            sku='SOLO-TONE',
            price=Decimal('50'),
            color_code='B',
            size_mm=22,
            size_a=25,
            size_b=26,
        )
        ProductImage.objects.create(product=solo, image=_png('solo.png'))
        _variants, colors, _sizes = build_variant_context(solo)
        self.assertEqual(len(colors), 1)
        self.assertTrue(colors[0]['img'])

    def test_family_falls_back_to_product_photo(self):
        ProductImage.objects.create(product=self.p_g, image=_png('prod.png'))
        _variants, colors, _sizes = build_variant_context(self.p_g)
        by_code = {c['code']: c for c in colors}
        self.assertTrue(by_code['G']['img'])
        self.assertEqual(by_code['N']['img'], '')

    def test_family_swatch_from_admin_image(self):
        FamilyColorSwatch.objects.create(
            family=self.family, color_code='G', image=_png('brass.png')
        )
        _variants, colors, _sizes = build_variant_context(self.p_g)
        by_code = {c['code']: c for c in colors}
        self.assertTrue(by_code['G']['img'])
        self.assertEqual(by_code['N']['img'], '')

    def test_pdp_has_no_family_label(self):
        page = self.client.get(
            reverse('catalog:product', args=[self.p_g.slug]), follow=True
        )
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'Сімʼя')
        self.assertNotContains(page, 'Плашка кольору')


class FamilyAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            'fadmin', 'f@example.com', 'pass12345'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.cat = Category.objects.create(name='Циліндри', slug='cyl-fam-admin')
        self.family = ProductFamily.objects.create(name='Модель X', slug='model-x')
        self.product = Product.objects.create(
            category=self.cat,
            name='Варіант 70 чорний',
            slug='var-70-b',
            sku='VAR-70-B',
            price=Decimal('200'),
            color_code='B',
            size_mm=70,
        )

    def test_family_changelist_and_form(self):
        listing = self.client.get(reverse('admin:catalog_productfamily_changelist'))
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, 'Модель X')
        page = self.client.get(
            reverse('admin:catalog_productfamily_change', args=[self.family.pk])
        )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Плашки кольорів')
        self.assertContains(page, 'id_products')
        self.assertContains(page, 'Варіанти')

    def test_assign_products_from_family_admin(self):
        url = reverse(
            'admin:catalog_productfamily_change', args=[self.family.pk]
        )
        payload = {
            'name': self.family.name,
            'slug': self.family.slug,
            'brand': '',
            'short_description': '',
            'description': '',
            'products': [str(self.product.pk)],
            'color_swatches-TOTAL_FORMS': '0',
            'color_swatches-INITIAL_FORMS': '0',
            'color_swatches-MIN_NUM_FORMS': '0',
            'color_swatches-MAX_NUM_FORMS': '3',
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.family_id, self.family.pk)

    def test_product_admin_hides_family(self):
        page = self.client.get(
            reverse('admin:catalog_product_change', args=[self.product.pk])
        )
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'id="id_family"')
