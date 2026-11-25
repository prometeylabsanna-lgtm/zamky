from django.test import Client, TestCase
from django.urls import reverse

from pages.models_cms import SiteSettings
from pages.phone import normalize_ua_tel


class PhoneNormalizeTests(TestCase):
    def test_ua_formatted(self):
        self.assertEqual(normalize_ua_tel("(067) 111 00 00"), "+380671110000")

    def test_already_e164(self):
        self.assertEqual(normalize_ua_tel("+380671110000"), "+380671110000")


class SitePhoneOnStorefrontTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings_obj = SiteSettings.load()

    def test_save_syncs_phone_raw_and_homepage(self):
        self.settings_obj.phone = "(067) 111 00 00"
        self.settings_obj.phone_raw = "+380670000000"
        self.settings_obj.save()
        self.settings_obj.refresh_from_db()
        self.assertEqual(self.settings_obj.phone_raw, "+380671110000")

        html = self.client.get(reverse("catalog:home")).content.decode()
        self.assertIn("(067) 111 00 00", html)
        self.assertIn("tel:+380671110000", html)
        self.assertNotIn("(067) 000 00 00", html)
        self.assertNotIn("tel:+380670000000", html)
