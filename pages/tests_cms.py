from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pages.admin_image_preview import admin_image_preview
from pages.content_manifest import JOB_TYPE, LANGUAGES, SITE_TYPE
from pages.models_cms import SiteSettings
from pages.site_content_registry import CONTENT_SECTIONS, get_section


class CmsManifestTests(TestCase):
    def test_manifest_basics(self):
        self.assertEqual(SITE_TYPE, "shop")
        self.assertEqual(JOB_TYPE, "retrofit_hardcode_kill")
        self.assertEqual(LANGUAGES, ("ua", "ru"))

    def test_registry_sections_unique(self):
        names = [s.admin_model_name for s in CONTENT_SECTIONS]
        self.assertEqual(len(names), len(set(names)))
        self.assertIsNotNone(get_section("home", "hero"))


class AdminImagePreviewTests(TestCase):
    def test_fallback_static(self):
        html = admin_image_preview(None, max_size=64, fallback_static="img/logo.png")
        self.assertIn("img/logo.png", html)
        self.assertIn("data-admin-img-preview", html)

    def test_empty_without_fallback(self):
        html = admin_image_preview(None)
        self.assertIn("—", html)


class CmsAdminSmokeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "cmsadmin", "cms@example.com", "pass12345"
        )
        SiteSettings.load()
        self.client = Client()
        self.client.force_login(self.user)

    def test_sitesettings_admin_200(self):
        url = reverse("admin:pages_sitesettings_change", args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_sitesettings_logo_favicon_preview(self):
        url = reverse("admin:pages_sitesettings_change", args=[1])
        response = self.client.get(url)
        self.assertContains(response, "data-admin-img-preview")
        self.assertContains(response, "img/logo.png")
        self.assertContains(response, "img/favicon-32x32.png")
        self.assertContains(response, "js/admin/image_preview.js")

    def test_home_hero_section_200(self):
        url = reverse("admin:pages_homeherosettings_changelist")
        response = self.client.get(url)
        self.assertIn(response.status_code, {200, 302})
        if response.status_code == 302:
            follow = self.client.get(response["Location"])
            self.assertEqual(follow.status_code, 200)
            self.assertContains(follow, "Банер")
            self.assertContains(follow, "site-content-editor__field--color")
            self.assertContains(follow, "zamky-cms-colorpick__hex")
