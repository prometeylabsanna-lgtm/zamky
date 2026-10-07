from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from .models import ContactRequest


@override_settings(ALLOWED_HOSTS=['*'])
class HeaderShellTests(TestCase):
    def tearDown(self):
        translation.deactivate_all()

    def test_header_renders_inventory(self):
        with translation.override('uk'):
            response = self.client.get(reverse('pages:info'))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('Каталог', body)
        self.assertIn('Новинки', body)
        self.assertIn('Про нас', body)
        self.assertIn('Наші контакти', body)
        self.assertIn('aria-label="Кошик"', body)
        self.assertIn('aria-label="Меню"', body)
        self.assertIn('aria-label="Закрити"', body)
        self.assertIn('aria-label="Оберіть район"', body)
        self.assertIn('>UA<', body)
        self.assertIn('data-set-lang="ru"', body)
        self.assertNotIn('data-set-lang="EN"', body)
        self.assertIn('Каталог товрів', body)
        self.assertIn('Замки. Всі права захищено', body)

    def test_lang_cookie_and_prefix(self):
        response = self.client.post('/lang/', {'lang': 'ru', 'next': '/uk/info/'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.cookies['zamky_lang'].value, 'ru')
        self.assertTrue(response.url.startswith('/ru/'))
        page = self.client.get('/ru/info/')
        self.assertContains(page, '>RU<')
        self.assertContains(page, 'Наши контакты')
        self.assertContains(page, 'Все права защищены')


@override_settings(ALLOWED_HOSTS=['*'])
class ContactRequestTests(TestCase):
    def setUp(self):
        self.client = Client()
        translation.deactivate_all()
        with translation.override('uk'):
            self.url = reverse('pages:contact')
            self.page_url = reverse('pages:info')

    def tearDown(self):
        translation.deactivate_all()

    def _valid(self, **extra):
        data = {
            'name': 'Олександр',
            'phone': '+380 67 000 00 00',
            'email': 'mail@example.com',
            'topic': ContactRequest.Topic.LOCK,
            'message': 'Потрібен підбір циліндра під двері 70 мм.',
            'consent': 'on',
            'idempotency_key': 'key-once-1234567890',
        }
        data.update(extra)
        return data

    def test_page_renders_inventory(self):
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('Про нас', body)
        self.assertIn('Як ми працюємо', body)
        self.assertIn('Торгова точка', body)
        self.assertIn('Залишилися питання?', body)
        self.assertIn('Написати нам', body)
        self.assertIn('Підбір замка або циліндра', body)
        self.assertContains(response, 'Договір оферти')
        self.assertContains(response, 'Політика конфіденційності')

    def test_valid_creates(self):
        response = self.client.post(self.url, self._valid())
        self.assertEqual(ContactRequest.objects.count(), 1)
        obj = ContactRequest.objects.get()
        self.assertEqual(obj.name, 'Олександр')
        self.assertTrue(obj.consent)
        self.assertIn('Дякуємо', response.content.decode())

    def test_invalid_errors(self):
        response = self.client.post(self.url, self._valid(name='A', phone='12', message='short'))
        self.assertEqual(ContactRequest.objects.count(), 0)
        body = response.content.decode()
        self.assertIn('Вкажіть ім’я', body)
        self.assertIn('Вкажіть номер у форматі +380 00 000 00 00', body)
        self.assertIn('від 10 символів', body)

    def test_no_consent(self):
        data = self._valid()
        data.pop('consent')
        response = self.client.post(self.url, data)
        self.assertEqual(ContactRequest.objects.count(), 0)
        self.assertIn('Потрібна згода на обробку даних', response.content.decode())

    def test_htmx_partial(self):
        response = self.client.post(
            self.url,
            self._valid(idempotency_key='htmx-key-1'),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/partials/contact_success.html')
        self.assertNotIn('<html', response.content.decode())
        self.assertEqual(ContactRequest.objects.count(), 1)

    def test_idempotent_no_duplicate(self):
        payload = self._valid(idempotency_key='same-key-abc')
        self.client.post(self.url, payload, HTTP_HX_REQUEST='true')
        self.client.post(self.url, payload, HTTP_HX_REQUEST='true')
        self.assertEqual(ContactRequest.objects.count(), 1)

    def test_russian_info_page(self):
        response = self.client.get('/ru/info/about/')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('О нас', body)
        self.assertIn('Как мы работаем', body)
        self.assertIn('Торговая точка', body)
