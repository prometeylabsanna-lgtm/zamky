from django.core.cache import cache
from django.test import TestCase
from django.utils import translation

from marketing.consent import COOKIE_NAME, VALUE_ALL, VALUE_NECESSARY, read_consent
from marketing.models import TrackingSettings


class CookieBannerTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_banner_stays_across_pages_until_click(self):
        home = self.client.get("/ua/").content.decode()
        catalog = self.client.get("/ua/catalog/").content.decode()
        about = self.client.get("/ua/info/about/").content.decode()
        for html in (home, catalog, about):
            self.assertIn('id="cookie-banner"', html)
            self.assertIn("data-cookie-consent=\"all\"", html)
            self.assertIn("data-cookie-consent=\"necessary\"", html)
            self.assertIn("/ua/info/privacy/", html)
            self.assertIn("has-cookie-banner", html)

    def test_accept_cookie_hides_banner_and_keeps_it_hidden(self):
        self.client.cookies[COOKIE_NAME] = VALUE_ALL
        home = self.client.get("/ua/").content.decode()
        catalog = self.client.get("/ua/catalog/").content.decode()
        self.assertNotIn('id="cookie-banner"', home)
        self.assertNotIn('id="cookie-banner"', catalog)
        self.assertNotIn("has-cookie-banner", home)

    def test_necessary_hides_banner_without_pixels(self):
        t = TrackingSettings.load()
        t.ga4_id = "G-ABC123XYZ"
        t.ga4_enabled = True
        t.save()
        self.client.cookies[COOKIE_NAME] = VALUE_NECESSARY
        html = self.client.get("/ua/").content.decode()
        self.assertNotIn('id="cookie-banner"', html)
        self.assertNotIn("G-ABC123XYZ", html)
        self.assertIn("gtag('consent','default'", html)
        self.assertNotIn("gtag('consent','update'", html)

    def test_unknown_cookie_does_not_count_as_choice(self):
        self.client.cookies[COOKIE_NAME] = "seen"
        html = self.client.get("/ua/").content.decode()
        self.assertIn('id="cookie-banner"', html)

    def test_ru_copy(self):
        with translation.override("ru"):
            html = self.client.get("/ru/").content.decode()
        self.assertIn("Мы используем файлы cookie", html)
        self.assertIn("Принять", html)
        self.assertIn("Только необходимые", html)
        self.assertIn("/ru/info/privacy/", html)


class ConsentHelperTests(TestCase):
    def test_read_consent_only_allows_known_values(self):
        class Req:
            COOKIES = {}

        req = Req()
        self.assertEqual(read_consent(req), "")
        req.COOKIES = {COOKIE_NAME: "all"}
        self.assertEqual(read_consent(req), "all")
        req.COOKIES = {COOKIE_NAME: "denied"}
        self.assertEqual(read_consent(req), "")
        self.assertEqual(read_consent(None), "")
