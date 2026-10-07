from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Category, Product
from orders.models import Order, OrderItem
from orders.utils import plural_positions


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

    def test_plural_positions(self):
        from django.utils import translation

        with translation.override('ua'):
            self.assertEqual(plural_positions(1), 'позиція')
            self.assertEqual(plural_positions(2), 'позиції')
            self.assertEqual(plural_positions(3), 'позиції')
            self.assertEqual(plural_positions(4), 'позиції')
            self.assertEqual(plural_positions(5), 'позицій')
            self.assertEqual(plural_positions(11), 'позицій')
            self.assertEqual(plural_positions(21), 'позиція')
            self.assertEqual(plural_positions(22), 'позиції')

    def test_totals_qty(self):
        """qty>1: cart / HTMX / checkout UI / Order(+delivery) / stock."""
        price = Decimal('1700.00')
        self.product.price = price
        self.product.old_price = Decimal('2000.00')
        self.product.stock = 10
        self.product.save()

        self._add_to_cart(2)
        expected_line = price * 2
        self.assertEqual(
            self.client.session['cart'][str(self.product.pk)]['qty'],
            2,
        )

        checkout = self.client.get(reverse('orders:checkout'))
        self.assertEqual(checkout.status_code, 200)
        body = checkout.content.decode()
        self.assertIn('3 400', body)
        self.assertContains(checkout, 'Оформлення замовлення')
        self.assertContains(checkout, 'checkout-steps')

        inc = self.client.post(
            reverse('cart:update', args=[self.product.pk]),
            {'action': 'inc'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(inc.status_code, 200)
        self.assertIn('5100', inc.content.decode())
        self.assertEqual(
            self.client.session['cart'][str(self.product.pk)]['qty'],
            3,
        )

        inc_checkout = self.client.post(
            reverse('cart:update', args=[self.product.pk]),
            {'action': 'inc', 'page': 'checkout'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(inc_checkout.status_code, 200)
        inc_body = inc_checkout.content.decode()
        self.assertIn('6 800', inc_body)
        # NP delivery 80 → order total 6880; OOB summary
        self.assertIn('6 880', inc_body)
        self.assertEqual(
            self.client.session['cart'][str(self.product.pk)]['qty'],
            4,
        )

        # повернути qty=2 для оформлення
        self.client.post(
            reverse('cart:update', args=[self.product.pk]),
            {'quantity': 2},
        )
        self.assertEqual(
            self.client.session['cart'][str(self.product.pk)]['qty'],
            2,
        )

        key = 'idem-totals-qty'
        session = self.client.session
        session['checkout_idempotency'] = key
        session.save()
        stock_before = self.product.stock
        response = self.client.post(
            reverse('orders:checkout') + '?step=checkout',
            {
                'first_name': 'Олег',
                'phone': '+380670000099',
                'city': 'Київ',
                'delivery_method': 'np',
                'payment_method': 'cod',
                'address': 'відділення 1',
                'idempotency_key': key,
            },
        )
        self.assertEqual(response.status_code, 302)

        order = Order.objects.get(idempotency_key=key)
        item = OrderItem.objects.get(order=order)
        self.assertEqual(item.unit_price, price)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.line_total, expected_line)
        self.assertEqual(order.subtotal, expected_line)
        self.assertEqual(order.delivery_price, Decimal('80.00'))
        self.assertEqual(order.total, expected_line + Decimal('80.00'))

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_before - 2)

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
        order = Order.objects.get()
        from orders.services import create_order_from_cart
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post('/')
        request.session = self.client.session
        existing, created = create_order_from_cart(
            request,
            {
                'first_name': 'Олег',
                'last_name': '',
                'phone': '0670000000',
                'email': '',
                'city': '',
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
