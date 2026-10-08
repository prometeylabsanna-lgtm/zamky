from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Category, Product


class CartTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Тест', slug='test')
        self.product = Product.objects.create(
            category=self.category,
            name='Тестовий циліндр',
            slug='test-cyl',
            sku='TEST-001',
            price=Decimal('400.00'),
            old_price=Decimal('520.00'),
            stock=5,
            is_active=True,
        )

    def test_add_to_cart(self):
        url = reverse('cart:add', args=[self.product.pk])
        response = self.client.post(url, {'quantity': 2})
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertEqual(session['cart'][str(self.product.pk)]['qty'], 2)

    def test_add_exceeds_stock(self):
        url = reverse('cart:add', args=[self.product.pk])
        response = self.client.post(url, {'quantity': 10})
        self.assertEqual(response.status_code, 400)

    def test_add_invalid_quantity(self):
        url = reverse('cart:add', args=[self.product.pk])
        response = self.client.post(url, {'quantity': 'abc'})
        self.assertEqual(response.status_code, 400)

    def test_add_open_redirect_blocked(self):
        url = reverse('cart:add', args=[self.product.pk])
        response = self.client.post(url, {'quantity': 1, 'next': 'https://evil.example/'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.example', response['Location'])

    def test_stock_clamp_sets_warning(self):
        from django.test import RequestFactory

        from cart.services import CartService

        self.client.post(reverse('cart:add', args=[self.product.pk]), {'quantity': 5})
        self.product.stock = 2
        self.product.save()
        factory = RequestFactory()
        request = factory.get('/')
        request.session = self.client.session
        cart = CartService(request)
        items = cart.items()
        self.assertEqual(items[0]['quantity'], 2)
        self.assertTrue(cart.warnings_text())

    def test_update_and_remove(self):
        self.client.post(reverse('cart:add', args=[self.product.pk]), {'quantity': 2})
        self.client.post(
            reverse('cart:update', args=[self.product.pk]),
            {'quantity': 1},
        )
        self.assertEqual(self.client.session['cart'][str(self.product.pk)]['qty'], 1)
        self.client.post(
            reverse('cart:update', args=[self.product.pk]),
            {'action': 'remove'},
        )
        self.assertNotIn(str(self.product.pk), self.client.session.get('cart', {}))

    def test_wishlist_toggle(self):
        url = reverse('cart:wishlist', args=[self.product.pk])
        self.client.post(url)
        self.assertIn(self.product.pk, self.client.session['wishlist'])
        self.client.post(url)
        self.assertNotIn(self.product.pk, self.client.session['wishlist'])

    def test_wishlist_page_and_card_toggle(self):
        page = self.client.get(reverse('cart:wishlist_page'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'У обраному поки порожньо')
        url = reverse('cart:wishlist', args=[self.product.pk])
        hx = self.client.post(
            url,
            {'variant': 'card'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(hx.status_code, 200)
        self.assertContains(hx, 'product-card__wish')
        self.assertContains(hx, 'is-active')
        self.assertContains(hx, 'wishlist-badge')
        page2 = self.client.get(reverse('cart:wishlist_page'))
        self.assertContains(page2, self.product.name)
        self.assertContains(page2, 'product-card__wish')
