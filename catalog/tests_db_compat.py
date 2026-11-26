from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from catalog.db_compat import published_reviews_for, review_table_ready
from catalog.models import Category, Product, Review


class ReviewSchemaCompatTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Замки', slug='locks-compat')
        self.product = Product.objects.create(
            category=self.cat,
            name='Замок тест',
            slug='lock-compat',
            sku='COMPAT-1',
            price=Decimal('100.00'),
        )

    def test_table_ready_in_tests(self):
        self.assertTrue(review_table_ready())

    def test_published_reviews_skip_missing_table(self):
        Review.objects.create(
            product=self.product,
            author_name='Ірина',
            rating=5,
            text='Ок',
            is_published=True,
        )
        with patch('catalog.db_compat.review_table_ready', return_value=False):
            self.assertEqual(published_reviews_for(self.product), [])
        self.assertEqual(len(published_reviews_for(self.product)), 1)

    def test_product_admin_without_review_table(self):
        User = get_user_model()
        user = User.objects.create_superuser('compat', 'c@example.com', 'pass12345')
        factory = RequestFactory()
        request = factory.get(
            reverse('admin:catalog_product_change', args=[self.product.pk])
        )
        request.user = user
        from catalog.admin import ProductAdmin, ProductImageInline
        from django.contrib.admin.sites import site

        admin = ProductAdmin(Product, site)
        with patch('catalog.db_compat.review_table_ready', return_value=False):
            self.assertEqual(admin.get_inlines(request, self.product), [ProductImageInline])
        page = self.client.get(reverse('admin:catalog_product_change', args=[self.product.pk]))
        self.assertEqual(page.status_code, 302)
        self.client.force_login(user)
        page = self.client.get(reverse('admin:catalog_product_change', args=[self.product.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Характеристики')
