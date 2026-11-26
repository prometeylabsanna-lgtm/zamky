import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import call_command
from django.db import IntegrityError
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from orders.models import Order
from orders.services import create_order_from_cart


class PaymentCheckoutTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.category = Category.objects.create(name='Тест', slug='test-pay')
        self.product = Product.objects.create(
            category=self.category,
            name='Замок оплата',
            slug='lock-pay',
            sku='PAY-001',
            price=Decimal('500.00'),
            stock=3,
            is_active=True,
        )

    def _add_to_cart(self, qty=1):
        self.client.post(reverse('cart:add', args=[self.product.pk]), {'quantity': qty})

    def _payload(self, key, payment_method='card'):
        return {
            'first_name': 'Олег',
            'phone': '0670000000',
            'delivery_method': 'pickup',
            'payment_method': payment_method,
            'idempotency_key': key,
        }

    def _checkout(self, key, payment_method='card'):
        session = self.client.session
        session['checkout_idempotency'] = key
        session.save()
        response = self.client.post(
            reverse('orders:checkout') + '?step=checkout',
            self._payload(key, payment_method),
        )
        self.assertEqual(response.status_code, 302, getattr(response, 'content', b'')[:300])
        return response

    def _cleaned(self, payment_method='card'):
        return {
            'first_name': 'Олег',
            'last_name': '',
            'phone': '0670000000',
            'email': '',
            'city': '',
            'district': None,
            'delivery_method': 'pickup',
            'payment_method': payment_method,
            'address': '',
            'comment': '',
        }

    def _sign(self, body: bytes, secret='dev-payment-webhook-secret'):
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    def _webhook(self, order, status='paid', ref=None, secret='dev-payment-webhook-secret'):
        payload = {
            'number': order.number,
            'payment_ref': order.payment_ref if ref is None else ref,
            'status': status,
        }
        body = json.dumps(payload).encode('utf-8')
        return self.client.post(
            reverse('payment_webhook'),
            data=body,
            content_type='application/json',
            HTTP_X_PAYMENT_SIGNATURE=self._sign(body, secret),
        )

    def test_cod_decrements_stock_and_stays_new(self):
        self._add_to_cart(1)
        response = self._checkout('idem-cod-new', 'cod')
        self.assertEqual(response.status_code, 302)
        self.assertIn('step=done', response['Location'])
        order = Order.objects.get(idempotency_key='idem-cod-new')
        self.assertEqual(order.status, Order.Status.NEW)
        self.assertFalse(order.reserved_until)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)

    def test_card_reserves_stock_and_redirects_to_wait(self):
        self._add_to_cart(1)
        response = self._checkout('idem-card-wait')
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(idempotency_key='idem-card-wait')
        self.assertIn(order.number, response['Location'])
        self.assertIn('/checkout/pay/', response['Location'])
        self.assertEqual(order.status, Order.Status.AWAITING_PAYMENT)
        self.assertTrue(order.payment_ref)
        self.assertIsNotNone(order.reserved_until)
        self.assertGreater(order.reserved_until, timezone.now())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)

    def test_double_post_same_key_no_500(self):
        self._add_to_cart(1)
        key = 'idem-double-http'
        r1 = self._checkout(key)
        self.assertEqual(r1.status_code, 302)
        session = self.client.session
        session['cart'] = {str(self.product.pk): {'qty': 1}}
        session['checkout_idempotency'] = key
        session.save()
        r2 = self.client.post(
            reverse('orders:checkout') + '?step=checkout',
            self._payload(key),
        )
        self.assertNotEqual(r2.status_code, 500)
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)

    def test_integrityerror_returns_existing(self):
        self._add_to_cart(1)
        key = 'idem-race-ie'
        r1 = self._checkout(key)
        self.assertEqual(r1.status_code, 302)
        order = Order.objects.get(idempotency_key=key)
        factory = RequestFactory()
        request = factory.post('/')
        request.session = self.client.session
        orig_filter = Order.objects.filter

        def selective(*args, **kwargs):
            if kwargs.get('idempotency_key') == key and not getattr(selective, 'skip_used', False):
                selective.skip_used = True
                return orig_filter(pk__in=[])
            return orig_filter(*args, **kwargs)

        with patch('orders.services.Order.objects.filter', selective):
            with patch(
                'orders.services._create_order_from_cart',
                side_effect=IntegrityError('dup'),
            ):
                existing, created = create_order_from_cart(
                    request, self._cleaned(), key
                )
        self.assertFalse(created)
        self.assertEqual(existing.pk, order.pk)
        self.assertEqual(Order.objects.count(), 1)

    def test_return_url_does_not_mark_paid(self):
        self._add_to_cart(1)
        self._checkout('idem-return')
        order = Order.objects.get(idempotency_key='idem-return')
        response = self.client.get(reverse('orders:pay_return', args=[order.number]))
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.AWAITING_PAYMENT)

    def test_wait_page_requires_session(self):
        self._add_to_cart(1)
        self._checkout('idem-wait-idor')
        order = Order.objects.get(idempotency_key='idem-wait-idor')
        ok = self.client.get(reverse('orders:pay_wait', args=[order.number]))
        self.assertEqual(ok.status_code, 200)
        other = Client()
        denied = other.get(reverse('orders:pay_wait', args=[order.number]))
        self.assertEqual(denied.status_code, 404)

    def test_webhook_marks_paid_once(self):
        self._add_to_cart(1)
        self._checkout('idem-hook')
        order = Order.objects.get(idempotency_key='idem-hook')
        stock_after_reserve = 2
        r1 = self._webhook(order)
        self.assertEqual(r1.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertIsNone(order.reserved_until)
        r2 = self._webhook(order)
        self.assertEqual(r2.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_after_reserve)
        self.assertEqual(Order.objects.filter(status=Order.Status.PAID).count(), 1)

    def test_release_expired_hold_restores_stock(self):
        self._add_to_cart(1)
        self._checkout('idem-hold')
        order = Order.objects.get(idempotency_key='idem-hold')
        order.reserved_until = timezone.now() - timedelta(minutes=1)
        order.save(update_fields=['reserved_until'])
        call_command('release_payment_holds')
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_webhook_after_cancel_does_not_revive(self):
        self._add_to_cart(1)
        self._checkout('idem-late-hook')
        order = Order.objects.get(idempotency_key='idem-late-hook')
        order.reserved_until = timezone.now() - timedelta(minutes=1)
        order.save(update_fields=['reserved_until'])
        call_command('release_payment_holds')
        self.product.refresh_from_db()
        stock_after = self.product.stock
        response = self._webhook(order)
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_after)

    def test_stub_pay_marks_paid(self):
        self._add_to_cart(1)
        self._checkout('idem-stub')
        order = Order.objects.get(idempotency_key='idem-stub')
        response = self.client.post(reverse('orders:pay_stub', args=[order.number]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)

    def test_paid_wait_redirects_to_done(self):
        self._add_to_cart(1)
        self._checkout('idem-paid-done')
        order = Order.objects.get(idempotency_key='idem-paid-done')
        self.client.post(reverse('orders:pay_stub', args=[order.number]))
        response = self.client.get(reverse('orders:pay_wait', args=[order.number]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('step=done', response['Location'])

    @override_settings(PAYMENT_WEBHOOK_SECRET='')
    def test_webhook_without_secret_is_forbidden(self):
        self._add_to_cart(1)
        self._checkout('idem-no-secret')
        order = Order.objects.get(idempotency_key='idem-no-secret')
        response = self._webhook(order, secret='')
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertNotEqual(order.status, Order.Status.PAID)

    def test_webhook_ref_mismatch_does_not_mark_paid(self):
        self._add_to_cart(1)
        self._checkout('idem-ref-bad')
        order = Order.objects.get(idempotency_key='idem-ref-bad')
        response = self._webhook(order, ref='not-the-ref')
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertNotEqual(order.status, Order.Status.PAID)

    def test_webhook_empty_ref_does_not_mark_paid(self):
        self._add_to_cart(1)
        self._checkout('idem-ref-empty')
        order = Order.objects.get(idempotency_key='idem-ref-empty')
        response = self._webhook(order, ref='')
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertNotEqual(order.status, Order.Status.PAID)

    @override_settings(PAYMENT_STUB_ENABLED=False, PAYMENT_ONLINE_ENABLED=False)
    def test_card_without_online_gateway_is_plain_order(self):
        self._add_to_cart(1)
        response = self._checkout('idem-card-offline')
        self.assertIn('step=done', response['Location'])
        order = Order.objects.get(idempotency_key='idem-card-offline')
        self.assertEqual(order.status, Order.Status.NEW)
        self.assertIsNone(order.reserved_until)
        self.assertFalse(order.payment_ref)

    @override_settings(PAYMENT_STUB_ENABLED=False, PAYMENT_ONLINE_ENABLED=False)
    def test_wait_page_without_gateway_shows_manager_message(self):
        self._add_to_cart(1)
        self._checkout('idem-wait-offline-msg')
        order = Order.objects.get(idempotency_key='idem-wait-offline-msg')
        order.status = Order.Status.AWAITING_PAYMENT
        order.save(update_fields=['status'])
        response = self.client.get(reverse('orders:pay_wait', args=[order.number]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Онлайн-оплата тимчасово недоступна. Менеджер звʼяжеться з вами, щоб узгодити оплату.',
        )

    def test_done_step_redirects_unpaid_card_to_wait(self):
        self._add_to_cart(1)
        self._checkout('idem-done-wait')
        order = Order.objects.get(idempotency_key='idem-done-wait')
        self.assertEqual(order.status, Order.Status.AWAITING_PAYMENT)
        response = self.client.get(reverse('orders:checkout') + '?step=done')
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('orders:pay_wait', args=[order.number]), response['Location'])
