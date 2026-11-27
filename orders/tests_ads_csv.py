from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from catalog.models import Category, Product
from orders.ads_csv import orders_ads_csv
from orders.models import Order, OrderItem


class OrdersAdsCsvTests(TestCase):
    def test_csv_has_city_address_and_items_without_payment_ref(self):
        category = Category.objects.create(name='Тест', slug='csv-cat')
        product = Product.objects.create(
            category=category,
            name='Замок',
            slug='csv-lock',
            sku='CSV-1',
            price=Decimal('100.00'),
            stock=2,
            is_active=True,
        )
        order = Order.objects.create(
            first_name='Олег',
            last_name='Коваленко',
            phone='0670000000',
            email='oleg@example.com',
            city='Львів',
            address='Відділення 12',
            payment_ref='secret-pay-ref',
            idempotency_key='csv-key-1',
            total=Decimal('100.00'),
            created_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            sku='CSV-1',
            unit_price=Decimal('100.00'),
            quantity=2,
            line_total=Decimal('200.00'),
        )
        body = orders_ads_csv(Order.objects.filter(pk=order.pk))
        self.assertTrue(body.startswith('\ufeff'))
        self.assertIn('Львів', body)
        self.assertIn('Відділення 12', body)
        self.assertIn('CSV-1 × 2', body)
        self.assertIn('oleg@example.com', body)
        self.assertNotIn('secret-pay-ref', body)
        self.assertNotIn('csv-key-1', body)
