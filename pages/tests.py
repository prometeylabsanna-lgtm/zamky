from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from .models import ContactRequest


@override_settings(ALLOWED_HOSTS=['*'])
class HeaderShellTests(TestCase):
    def tearDown(self):
        translation.deactivate_all()

    def test_header_renders_inventory(self):
        with translation.override('ua'):
            response = self.client.get(reverse('pages:info'))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('Каталог товарів', body)
        self.assertIn('Акції', body)
        self.assertIn('Установка', body)
        self.assertIn('Замовити дзвінок', body)
        self.assertIn('aria-label="Кошик"', body)
        self.assertIn('aria-label="Меню"', body)
        self.assertIn('aria-label="Закрити"', body)
        self.assertIn('>UA<', body)
        self.assertIn('data-set-lang="ru"', body)
        self.assertNotIn('data-set-lang="EN"', body)
        self.assertIn('Центр замків', body)
        self.assertIn('PrometeyLabs', body)
        self.assertNotIn('site-footer__credit-link', body)

    def test_lang_cookie_and_prefix(self):
        response = self.client.post('/lang/', {'lang': 'ru', 'next': '/ua/info/'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.cookies['zamky_lang'].value, 'ru')
        self.assertTrue(response.url.startswith('/ru/'))
        page = self.client.get('/ru/info/')
        self.assertContains(page, '>RU<')
        self.assertContains(page, 'Сайт создан в')
        back = self.client.post('/lang/', {'lang': 'ua', 'next': '/ru/catalog/'})
        self.assertEqual(back.status_code, 302)
        self.assertTrue(back.url.startswith('/ua/'))


CREDIT_URL = 'https://www.prometeylabs.com/internet-shop-v2/'


@override_settings(ALLOWED_HOSTS=['*'])
class FooterDeveloperLinkTests(TestCase):
    def tearDown(self):
        translation.deactivate_all()

    def test_home_has_nofollow_credit_link(self):
        with translation.override('ua'):
            response = self.client.get(reverse('catalog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, CREDIT_URL)
        self.assertContains(response, 'nofollow')
        self.assertContains(response, '>PrometeyLabs</a>')
        self.assertContains(response, 'Центр замків')

    def test_localized_home_keeps_credit_link(self):
        for path in ('/ua/', '/ru/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, CREDIT_URL)
            self.assertContains(response, 'site-footer__credit-link')

    def test_inner_pages_show_credit_without_link(self):
        for path in ('/ua/catalog/', '/ua/info/privacy/', '/ua/info/about/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'PrometeyLabs')
            self.assertNotContains(response, CREDIT_URL)
            self.assertNotContains(response, 'site-footer__credit-link')


@override_settings(ALLOWED_HOSTS=['*'])
class ContactFormTests(TestCase):
    def tearDown(self):
        translation.deactivate_all()

    def test_contact_submit_creates_request(self):
        with translation.override('ua'):
            page = self.client.get(reverse('pages:info_page', kwargs={'page': 'about'}))
        self.assertEqual(page.status_code, 200)
        key = self.client.session.get('contact_idempotency')
        self.assertTrue(key)
        response = self.client.post(
            reverse('pages:contact'),
            {
                'name': 'Олег',
                'phone': '+380670000001',
                'email': 'a@b.co',
                'topic': 'lock',
                'message': 'Потрібен підбір замка для дверей',
                'consent': 'on',
                'idempotency_key': key,
            },
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactRequest.objects.count(), 1)


@override_settings(ALLOWED_HOSTS=['*'])
class DesignV2EndpointsTests(TestCase):
    def tearDown(self):
        translation.deactivate_all()

    def test_info_pages_ok(self):
        for slug in ('delivery', 'warranty', 'returns', 'install', 'promos', 'about'):
            with translation.override('ua'):
                r = self.client.get(reverse('pages:info_page', kwargs={'page': slug}))
            self.assertEqual(r.status_code, 200, slug)

    def test_blog_list(self):
        with translation.override('ua'):
            r = self.client.get(reverse('pages:blog_list'))
        self.assertEqual(r.status_code, 200)

    def test_callback_post(self):
        with translation.override('ua'):
            self.client.get(reverse('catalog:home'))
        key = self.client.session.get('callback_idempotency')
        r = self.client.post(
            reverse('pages:callback'),
            {'phone': '+380670000002', 'name': 'Тест', 'idempotency_key': key},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(r.status_code, 200)

    def test_picker_api(self):
        with translation.override('ua'):
            r = self.client.get(reverse('catalog:api_picker'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('application/json', r['Content-Type'])
