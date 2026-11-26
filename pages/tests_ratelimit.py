from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from config.ratelimit import FORM_LIMIT, LOGIN_LIMIT


@override_settings(ALLOWED_HOSTS=['*'])
class RateLimitTests(TestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()
        translation.deactivate_all()

    def _contact_payload(self):
        return {
            'name': 'Олег',
            'phone': '+380670000001',
            'email': 'a@b.co',
            'topic': 'lock',
            'message': 'Потрібен підбір замка для дверей',
            'consent': 'on',
        }

    def test_contact_ninth_post_is_429(self):
        with translation.override('ua'):
            self.client.get(reverse('pages:info_page', kwargs={'page': 'about'}))
        url = reverse('pages:contact')
        payload = self._contact_payload()
        for i in range(FORM_LIMIT):
            response = self.client.post(url, payload, HTTP_HX_REQUEST='true')
            self.assertEqual(response.status_code, 200, i)
        blocked = self.client.post(url, payload, HTTP_HX_REQUEST='true')
        self.assertEqual(blocked.status_code, 429)
        self.assertIn('Забагато', blocked.content.decode())

    def test_ignores_x_forwarded_for(self):
        with translation.override('ua'):
            self.client.get(reverse('pages:info_page', kwargs={'page': 'about'}))
        url = reverse('pages:contact')
        payload = self._contact_payload()
        for i in range(FORM_LIMIT):
            self.client.post(
                url,
                payload,
                HTTP_HX_REQUEST='true',
                HTTP_X_FORWARDED_FOR=f'1.1.1.{i}',
            )
        blocked = self.client.post(
            url,
            payload,
            HTTP_HX_REQUEST='true',
            HTTP_X_FORWARDED_FOR='9.9.9.9',
        )
        self.assertEqual(blocked.status_code, 429)

    def test_x_real_ip_separate_buckets(self):
        with translation.override('ua'):
            self.client.get(reverse('pages:info_page', kwargs={'page': 'about'}))
        url = reverse('pages:contact')
        payload = self._contact_payload()
        for _ in range(FORM_LIMIT):
            self.client.post(
                url,
                payload,
                HTTP_HX_REQUEST='true',
                HTTP_X_REAL_IP='10.0.0.1',
            )
        other = self.client.post(
            url,
            payload,
            HTTP_HX_REQUEST='true',
            HTTP_X_REAL_IP='10.0.0.2',
        )
        self.assertEqual(other.status_code, 200)
        blocked = self.client.post(
            url,
            payload,
            HTTP_HX_REQUEST='true',
            HTTP_X_REAL_IP='10.0.0.1',
        )
        self.assertEqual(blocked.status_code, 429)

    def test_admin_login_ninth_post_is_429(self):
        url = reverse('admin:login')
        for i in range(LOGIN_LIMIT):
            response = self.client.post(url, {'username': 'x', 'password': 'bad'})
            self.assertIn(response.status_code, (200, 302), i)
        blocked = self.client.post(url, {'username': 'x', 'password': 'bad'})
        self.assertEqual(blocked.status_code, 429)
