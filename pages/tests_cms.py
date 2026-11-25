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

    def test_localized_admin_url_redirects(self):
        resp = self.client.get("/ua/admin/", follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp["Location"].startswith("/admin/"))

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

    def test_home_audience_icons_visible(self):
        url = reverse("admin:pages_homeaudiencesettings_changelist")
        response = self.client.get(url)
        self.assertIn(response.status_code, {200, 302})
        page = response
        if response.status_code == 302:
            page = self.client.get(response["Location"])
            self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Картка 1 — іконка")
        self.assertContains(page, "site-content-editor__img-preview--icon")
        self.assertContains(page, "cms-icon-preview")
        self.assertContains(page, "img/v2/audience/icon-home.svg")
        self.assertContains(page, "img/v2/audience/icon-biz.svg")
        self.assertContains(page, 'type="file"')
        self.assertContains(page, "стандартна іконка")
        self.assertNotContains(page, "cms-icon-pick")

    def test_home_audience_uses_static_icon_preview(self):
        response = self.client.get("/ua/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "img/v2/audience/icon-home.svg")
        self.assertContains(response, "home-audience__icon")

    def test_home_categories_admin_has_no_unused_title(self):
        url = reverse("admin:pages_homecategoriessettings_changelist")
        response = self.client.get(url)
        self.assertIn(response.status_code, {200, 302})
        page = response
        if response.status_code == 302:
            page = self.client.get(response["Location"])
            self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Додати")
        self.assertNotContains(page, "Заголовок категорій")
        self.assertNotContains(page, "Підпис категорії 1")
        self.assertNotContains(page, "categories_title")

    def test_footer_admin_has_no_unused_about_title(self):
        url = reverse("admin:pages_sitefootersettings_change", args=[1])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Підвал — про нас (текст)")
        self.assertNotContains(page, "Підвал — про нас (заголовок)")
        self.assertNotContains(page, "footer_about_title")

    def test_catalog_filters_title_hint_is_mobile(self):
        url = reverse("admin:pages_catalogchromesettings_change", args=[1])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Заголовок фільтрів")
        self.assertContains(page, "на мобільному та планшеті")
        self.assertContains(page, "На десктопі не показується")
