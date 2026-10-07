from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Category, Product
from orders.models import Order


class CheckoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Тест', slug='test-ord')
        self.product = Product.objects.create(
            category=self.category,
            name='Замок тест',
            slug='lock-test',
            sku='ORD-001',
            price=Decimal('500.00'),
            stock=3,
            is_active=True,
        )

    def _add_to_cart(self, qty=1):
        self.client.post(reverse('cart:add', args=[self.product.pk]), {'quantity': qty})

    def test_checkout_decrements_stock(self):
        self._add_to_cart(2)
        key = 'idem-stock-1'
        session = self.client.session
        session['checkout_idempotency'] = key
        session.save()
        response = self.client.post(
            reverse('orders:checkout') + '?step=checkout',
            {
                'first_name': 'Олег',
                'phone': '+380670000000',
                'delivery_method': 'pickup',
                'payment_method': 'cod',
                'idempotency_key': key,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertEqual(Order.objects.count(), 1)

    def test_idempotency_no_double_order(self):
        self._add_to_cart(1)
        key = 'idem-double-1'
        session = self.client.session
        session['checkout_idempotency'] = key
        session.save()
        payload = {
            'first_name': 'Олег',
            'phone': '0670000000',
            'delivery_method': 'pickup',
            'payment_method': 'cod',
            'idempotency_key': key,
        }
        r1 = self.client.post(reverse('orders:checkout') + '?step=checkout', payload)
        self.assertEqual(r1.status_code, 302)
        # повторна відправка того ж ключа після очистки кошика
        order = Order.objects.get()
        from orders.services import create_order_from_cart

        class Req:
            session = self.client.session

        # emulate second submit with same key via service
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post('/')
        request.session = self.client.session
        # cart empty now; still return existing order
        existing, created = create_order_from_cart(
            request,
            {
                'first_name': 'Олег',
                'last_name': '',
                'phone': '0670000000',
                'email': '',
                'district': None,
                'delivery_method': 'pickup',
                'payment_method': 'cod',
                'address': '',
                'comment': '',
            },
            key,
        )
        self.assertFalse(created)
        self.assertEqual(existing.pk, order.pk)
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)

    def test_checkout_blocks_over_stock(self):
        self.product.stock = 1
        self.product.save()
        self._add_to_cart(1)
        # artificially inflate session qty
        session = self.client.session
        session['cart'] = {str(self.product.pk): {'qty': 5}}
        session['checkout_idempotency'] = 'idem-over'
        session.save()
        response = self.client.post(
            reverse('orders:checkout') + '?step=checkout',
            {
                'first_name': 'Олег',
                'phone': '0670000000',
                'delivery_method': 'pickup',
                'payment_method': 'cod',
                'idempotency_key': 'idem-over',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
