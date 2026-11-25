from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Category
from pages.models_cms import SiteSettings
from pages.models_page_style import PageStyle


class HomeCategoriesCmsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "catadmin", "cat@example.com", "pass12345"
        )
        SiteSettings.load()
        self.client = Client()
        self.client.force_login(self.user)
        self.cat = Category.objects.create(
            name="Серцевини (циліндри)",
            slug="cyl-test",
            home_subtitle="Врізні, накладні",
            sort_order=0,
            is_active=True,
        )

    def _admin_page(self, extra=""):
        url = reverse("admin:pages_homecategoriessettings_changelist")
        response = self.client.get(url)
        if response.status_code == 302:
            loc = response["Location"]
            if extra:
                sep = "&" if "?" in loc else "?"
                loc = f"{loc}{sep}{extra.lstrip('?')}"
            response = self.client.get(loc)
        elif extra:
            change = reverse(
                "admin:pages_homecategoriessettings_change", args=[1]
            )
            response = self.client.get(f"{change}?{extra.lstrip('?')}")
        return response

    def test_nav_uses_real_names(self):
        page = self._admin_page()
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Серцевини (циліндри)")
        self.assertContains(page, "Додати")
        self.assertContains(page, "home-cat-admin-nav")
        self.assertNotContains(page, "Категорія 1")

    def test_detail_has_preview_name_subtitle(self):
        page = self._admin_page(f"cat={self.cat.pk}")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "home-cat-admin-preview")
        self.assertContains(page, 'name="name"')
        self.assertContains(page, 'name="home_subtitle"')
        self.assertContains(page, 'type="file"')
        self.assertContains(page, "Врізні, накладні")

    def test_add_appends_last_and_shows_on_home(self):
        change = reverse("admin:pages_homecategoriessettings_change", args=[1])
        response = self.client.post(
            f"{change}?new=1",
            {
                "section_visible": "on",
                "style_background": PageStyle.DEFAULT_BACKGROUND,
                "style_text": PageStyle.DEFAULT_TEXT,
                "style_accent": PageStyle.DEFAULT_ACCENT,
                "card_new": "1",
                "name": "Нова картка",
                "name_ru": "",
                "home_subtitle": "Підпис нової",
                "home_subtitle_ru": "",
                "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        created = Category.objects.get(name="Нова картка")
        self.assertGreater(created.sort_order, self.cat.sort_order)
        home = self.client.get("/ua/")
        self.assertContains(home, "Нова картка")
        self.assertContains(home, "Підпис нової")
        self.assertContains(home, created.get_absolute_url())
