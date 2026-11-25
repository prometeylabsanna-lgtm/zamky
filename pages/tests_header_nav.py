from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from pages.header_nav import (
    ensure_default_header_nav,
    get_header_nav_links,
    localize_href,
    nav_style,
)
from pages.models_cms import SiteSettings
from pages.models_header import HeaderNavLink


class HeaderNavCmsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "hdradmin", "hdr@example.com", "pass12345"
        )
        SiteSettings.load()
        HeaderNavLink.objects.all().delete()
        ensure_default_header_nav()
        self.client = Client()
        self.client.force_login(self.user)

    def tearDown(self):
        translation.deactivate_all()

    def _admin(self):
        return reverse("admin:pages_siteheadersettings_change", args=[1])

    def test_admin_shows_nav_rows(self):
        page = self.client.get(self._admin())
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Кнопки навігації")
        self.assertContains(page, "Циліндри")
        self.assertContains(page, "Акції")
        self.assertContains(page, "Додати кнопку")

    def test_frontend_renders_seeded_buttons(self):
        with translation.override("ua"):
            page = self.client.get("/ua/")
        body = page.content.decode()
        self.assertIn("hdr-nav__link", body)
        self.assertIn("Циліндри", body)
        self.assertIn("hdr-nav__promo", body)
        self.assertIn("hdr-nav__install", body)
        self.assertIn("/ua/info/promos/", body)

    def test_hidden_button_not_on_site(self):
        HeaderNavLink.objects.filter(key="cyl").update(is_active=False)
        with translation.override("ua"):
            page = self.client.get("/ua/")
        body = page.content.decode()
        nav = body[body.index('class="hdr-nav"') : body.index("</nav>", body.index('class="hdr-nav"'))]
        self.assertNotIn("Циліндри", nav)

    def test_ru_label_and_prefix(self):
        rows = get_header_nav_links("ru")
        promo = next(item for item in rows if item["key"] == "promos")
        self.assertEqual(promo["name"], "Акции")
        self.assertTrue(promo["href"].startswith("/ru/"))
        with translation.override("ru"):
            page = self.client.get("/ru/")
        self.assertContains(page, "Акции")

    def test_localize_and_style(self):
        self.assertEqual(localize_href("/ua/info/promos/", "ru"), "/ru/info/promos/")
        self.assertEqual(nav_style("/ua/info/promos/", "promos"), "promo")
        self.assertEqual(nav_style("/ua/info/install/", "install"), "install")
        self.assertEqual(nav_style("/ua/catalog/?q=Cisa", "cisa"), "link")

    def test_formset_hides_and_reorders(self):
        from pages.admin_header_nav import build_header_nav_formset

        fs = build_header_nav_formset()
        data = {f"header_nav-{k}": v for k, v in fs.management_form.initial.items()}
        forms = fs.initial_forms
        data["header_nav-TOTAL_FORMS"] = str(len(forms))
        for i, form in enumerate(forms):
            inst = form.instance
            data[f"header_nav-{i}-id"] = str(inst.pk)
            data[f"header_nav-{i}-key"] = inst.key
            data[f"header_nav-{i}-name"] = inst.name
            data[f"header_nav-{i}-name_ru"] = inst.name_ru
            data[f"header_nav-{i}-url"] = inst.url
            data[f"header_nav-{i}-sort_order"] = str(i)
            if inst.key != "hardware":
                data[f"header_nav-{i}-is_active"] = "on"
        data["header_nav-0-sort_order"] = "9"
        good = build_header_nav_formset(data=data)
        self.assertTrue(good.is_valid(), good.errors)
        good.save()
        hardware = HeaderNavLink.objects.get(key="hardware")
        self.assertFalse(hardware.is_active)
        first = HeaderNavLink.objects.get(key="locks")
        self.assertEqual(first.sort_order, 9)
