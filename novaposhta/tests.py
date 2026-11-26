from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product
from novaposhta.client import NPApiError
from novaposhta.models import NPCity, NPSyncRun, NPWarehouse
from novaposhta.normalize import city_search_norm, warehouse_search_norm
from novaposhta.search import search_cities, search_warehouses
from novaposhta.sync import sync_warehouses
from orders.models import Order

CITY_A = '11111111-1111-4111-8111-111111111111'
CITY_B = '22222222-2222-4222-8222-222222222222'
REF_A = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
REF_B = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
REF_C = 'cccccccc-cccc-4ccc-8ccc-cccccccccccc'


def _row(ref, number, city_ref=CITY_A, city_name='Київ', description='Відділення', category='Branch'):
    return {
        'Ref': ref,
        'Number': number,
        'Description': description,
        'DescriptionRu': description,
        'ShortAddress': 'вул. Тестова, 1',
        'ShortAddressRu': 'ул. Тестовая, 1',
        'TypeOfWarehouse': 'type-ref',
        'CategoryOfWarehouse': category,
        'CityRef': city_ref,
        'CityDescription': city_name,
        'CityDescriptionRu': city_name,
        'SettlementAreaDescription': 'Київська',
        'SettlementRegionsDescription': '',
        'SettlementTypeDescription': 'місто',
        'WarehouseStatus': 'Working',
        'DenyToSelect': '0',
        'TotalMaxWeightAllowed': '30',
    }


class _PagesClient:
    def __init__(self, pages):
        self.pages = pages

    def get_warehouses(self, page, limit):
        index = page - 1
        rows = self.pages[index] if 0 <= index < len(self.pages) else []
        return {'success': True, 'data': rows, 'info': {'totalCount': 1000}}


class NovaPoshtaTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client_http = self.client
        self.category = Category.objects.create(name='Тест', slug='test-np')
        self.product = Product.objects.create(
            category=self.category,
            name='Замок тест',
            slug='lock-np',
            sku='NP-001',
            price=Decimal('500.00'),
            stock=3,
            is_active=True,
        )

    def tearDown(self):
        cache.clear()

    def test_sync_pages_update_and_failed_keeps_active(self):
        first = _PagesClient(
            [
                [_row(REF_A, '1'), _row(REF_B, '2', city_ref=CITY_B, city_name='Львів')],
                [_row(REF_C, '3', description='Третя')],
            ]
        )
        run = sync_warehouses(client=first, limit=2, max_pages=10)
        self.assertEqual(run.status, NPSyncRun.Status.SUCCESS)
        self.assertEqual(NPWarehouse.objects.filter(is_active=True).count(), 3)
        self.assertEqual(NPCity.objects.filter(is_active=True).count(), 2)

        second = _PagesClient(
            [
                [_row(REF_A, '1')],
                [_row(REF_C, '3', description='Оновлена')],
            ]
        )
        again = sync_warehouses(client=second, limit=2, max_pages=10)
        self.assertEqual(again.status, NPSyncRun.Status.SUCCESS)
        self.assertEqual(again.created, 0)
        self.assertEqual(again.updated, 2)
        self.assertEqual(again.deactivated, 1)
        self.assertEqual(NPWarehouse.objects.get(ref=REF_C).description, 'Оновлена')
        self.assertFalse(NPWarehouse.objects.get(ref=REF_B).is_active)
        self.assertFalse(NPCity.objects.get(ref=CITY_B).is_active)
        self.assertTrue(NPCity.objects.get(ref=CITY_A).is_active)

        NPWarehouse.objects.filter(ref=REF_B).update(is_active=True)

        class Boom:
            def get_warehouses(self, page, limit):
                if page == 1:
                    return {
                        'success': True,
                        'data': [_row(REF_A, '1', description='З першої')],
                        'info': {'totalCount': 1000},
                    }
                raise NPApiError('збій другої сторінки')

        failed = sync_warehouses(client=Boom(), limit=2, max_pages=10)
        self.assertEqual(failed.status, NPSyncRun.Status.FAILED)
        self.assertIn('збій', failed.message)
        self.assertEqual(failed.deactivated, 0)
        self.assertTrue(NPWarehouse.objects.get(ref=REF_B).is_active)
        self.assertTrue(NPWarehouse.objects.get(ref=REF_C).is_active)

    def test_search_cities_from_two_characters(self):
        NPCity.objects.create(
            ref=CITY_A,
            name='Київ',
            name_ru='Киев',
            area='Київська',
            is_active=True,
            search_norm=city_search_norm('Київ', 'Киев', 'Київська'),
        )
        self.assertEqual(search_cities('к'), [])
        self.assertTrue(any(city.name == 'Київ' for city in search_cities('ки')))
        self.assertTrue(any(city.name == 'Київ' for city in search_cities('КИЇВ')))
        self.assertTrue(any(city.name == 'Київ' for city in search_cities('rb]d')))

    def test_search_warehouse_by_number(self):
        def add(ref, number, category, city_ref=CITY_A, selectable=True):
            return NPWarehouse.objects.create(
                ref=ref,
                number=str(number),
                number_int=int(number),
                category=category,
                description=f'Відділення №{number}',
                description_ru=f'Отделение №{number}',
                short_address='вул. Хрещатик, 1',
                city_ref=city_ref,
                city_name='Київ',
                city_name_ru='Киев',
                is_active=True,
                is_selectable=selectable,
                search_norm=warehouse_search_norm(
                    str(number),
                    f'Відділення №{number}',
                    f'Отделение №{number}',
                    'вул. Хрещатик, 1',
                    '',
                    'Київ',
                    'Киев',
                ),
            )

        add(REF_A, 12, 'Branch')
        add('dddddddd-dddd-4ddd-8ddd-dddddddddddd', 12, 'Postomat')
        add('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee', 12, 'Cargo')
        add('ffffffff-ffff-4fff-8fff-ffffffffffff', 120, 'Postomat')
        add(REF_B, 12, 'Branch', selectable=False)
        add(REF_C, 12, 'Branch', city_ref=CITY_B)

        for query in ('№12', 'відділення 12', '12'):
            found = search_warehouses(query, city_ref=CITY_A)
            self.assertTrue(found, query)
            self.assertEqual(found[0].number, '12')
            self.assertEqual(found[0].category, 'Branch')
            self.assertTrue(found[0].is_selectable)
            self.assertTrue(all(row.category != 'Cargo' for row in found))
            self.assertTrue(all(row.city_ref == CITY_A for row in found))
            self.assertTrue(all(row.is_selectable for row in found))

    def test_checkout_saves_warehouse_and_rejects_other_city(self):
        NPWarehouse.objects.create(
            ref=REF_A,
            number='12',
            number_int=12,
            category='Branch',
            description='Відділення №12',
            city_ref=CITY_A,
            city_name='Київ',
            is_active=True,
            is_selectable=True,
            search_norm='12',
        )
        NPWarehouse.objects.create(
            ref=REF_B,
            number='3',
            number_int=3,
            category='Branch',
            description='Відділення №3',
            city_ref=CITY_B,
            city_name='Львів',
            is_active=True,
            is_selectable=True,
            search_norm='3',
        )
        self.client_http.post(reverse('cart:add', args=[self.product.pk]), {'quantity': 1})
        key = 'idem-np-wh'
        session = self.client_http.session
        session['checkout_idempotency'] = key
        session.save()
        url = reverse('orders:checkout') + '?step=checkout'
        mismatch = self.client_http.post(
            url,
            {
                'first_name': 'Олег',
                'phone': '+380670000099',
                'city': 'Київ',
                'address': 'чуже',
                'delivery_method': 'np',
                'payment_method': 'cod',
                'np_city_ref': CITY_A,
                'np_warehouse_ref': REF_B,
                'idempotency_key': key,
            },
        )
        self.assertEqual(mismatch.status_code, 200)
        self.assertContains(mismatch, 'Відділення не належить обраному місту')
        self.assertEqual(Order.objects.count(), 0)

        saved = self.client_http.post(
            url,
            {
                'first_name': 'Олег',
                'phone': '+380670000099',
                'city': 'Київ',
                'address': 'чернетка',
                'delivery_method': 'np',
                'payment_method': 'cod',
                'np_city_ref': CITY_A,
                'np_warehouse_ref': REF_A,
                'idempotency_key': key,
            },
        )
        self.assertEqual(saved.status_code, 302)
        order = Order.objects.get(idempotency_key=key)
        self.assertEqual(order.np_city_ref, CITY_A)
        self.assertEqual(order.np_warehouse_ref, REF_A)
        self.assertEqual(order.np_warehouse_snapshot, 'Відділення №12')
        self.assertIn('Відділення №12', order.address)

    def test_manual_checkout_and_command_without_directory(self):
        endpoint = self.client_http.get(reverse('novaposhta:warehouses'))
        self.assertEqual(endpoint.status_code, 200)
        self.assertEqual(endpoint.json(), {'available': False, 'items': []})
        self.assertEqual(endpoint['X-Robots-Tag'], 'noindex, nofollow')

        self.client_http.post(reverse('cart:add', args=[self.product.pk]), {'quantity': 1})
        key = 'idem-np-manual'
        session = self.client_http.session
        session['checkout_idempotency'] = key
        session.save()
        response = self.client_http.post(
            reverse('orders:checkout') + '?step=checkout',
            {
                'first_name': 'Олег',
                'phone': '+380670000099',
                'city': 'Київ',
                'address': 'відділення 1',
                'delivery_method': 'np',
                'payment_method': 'cod',
                'idempotency_key': key,
            },
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(idempotency_key=key)
        self.assertEqual(order.np_warehouse_ref, '')
        self.assertIn('відділення 1', order.address)

        with patch('novaposhta.sync.NovaPoshtaClient') as client_cls:
            client_cls.return_value.get_warehouses.side_effect = NPApiError('немає звʼязку')
            with self.assertRaises(CommandError):
                call_command('sync_np_warehouses')
        run = NPSyncRun.objects.latest('started_at')
        self.assertEqual(run.status, NPSyncRun.Status.FAILED)
        self.assertTrue(run.message)
        self.assertNotIn('apiKey', run.message)
