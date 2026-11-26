from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from pages.legal_body import default_offer_html, sanitize_legal_html
from pages.models_cms import SiteSettings, clear_site_blocks_cache
from pages.site_content_registry import get_section


class LegalBodyCmsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "legaladmin", "legal@example.com", "pass12345"
        )
        SiteSettings.load()
        self.client = Client()
        self.client.force_login(self.user)

    def tearDown(self):
        translation.deactivate_all()

    def test_registry_has_single_body_field(self):
        offer = get_section("offer", "body")
        privacy = get_section("privacy", "body")
        self.assertIn(("offer", "offer_body"), offer.blocks)
        self.assertNotIn(("offer", "offer_sec_1_title"), offer.blocks)
        self.assertIn(("privacy", "privacy_body"), privacy.blocks)
        self.assertNotIn(("privacy", "privacy_collect_1"), privacy.blocks)

    def test_admin_uses_tinymce(self):
        url = reverse("admin:pages_offerbodysettings_change", args=[1])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "cms-tinymce")
        self.assertContains(page, "Текст сторінки")
        self.assertNotContains(page, "Розділ 1 — заголовок")

    def test_offer_page_renders_headings(self):
        clear_site_blocks_cache()
        with translation.override("ua"):
            page = self.client.get("/ua/info/offer/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "info-legal")
        self.assertContains(page, "Загальні положення")
        self.assertContains(page, "<h2>", html=False)
        self.assertNotContains(page, "положення11")

    def test_privacy_page_renders_list(self):
        clear_site_blocks_cache()
        with translation.override("ua"):
            page = self.client.get("/ua/info/privacy/")
        self.assertContains(page, "Які дані ми збираємо")
        self.assertContains(page, "<ul>", html=False)
        self.assertContains(page, "info-callout")

    def test_sanitize_drops_script(self):
        raw = '<p>ok</p><script>alert(1)</script><h2>T</h2>'
        clean = sanitize_legal_html(raw)
        self.assertIn("<p>ok</p>", clean)
        self.assertIn("<h2>T</h2>", clean)
        self.assertNotIn("script", clean.lower())

    def test_sanitize_href_allowlist(self):
        clean = sanitize_legal_html(
            '<a href="javascript:alert(1)">x</a>'
            '<a href="data:text/html,hi">y</a>'
            '<a href="vbscript:x">z</a>'
            '<a href="https://ok.example/p">ok</a>'
            '<a href="/ua/catalog/">rel</a>'
        )
        self.assertNotIn("javascript", clean.lower())
        self.assertNotIn("data:", clean.lower())
        self.assertNotIn("vbscript", clean.lower())
        self.assertIn("https://ok.example/p", clean)
        self.assertIn("/ua/catalog/", clean)

    def test_default_html_has_structure(self):
        html = default_offer_html("ua")
        self.assertIn("<h2>", html)
        self.assertIn("<blockquote>", html)
        self.assertIn("Покупець", html)
