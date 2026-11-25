from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from pages.footer_nav import ensure_default_footer_nav, get_footer_nav
from pages.models_cms import SiteSettings
from pages.models_footer import FooterNavLink


class FooterNavCmsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "ftadmin", "ft@example.com", "pass12345"
        )
        SiteSettings.load()
        FooterNavLink.objects.all().delete()
        ensure_default_footer_nav()
        self.client = Client()
        self.client.force_login(self.user)

    def tearDown(self):
        translation.deactivate_all()

    def _admin(self):
        return reverse("admin:pages_sitefootersettings_change", args=[1])

    def test_admin_shows_grouped_rows(self):
        page = self.client.get(self._admin())
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Колонка «Каталог»")
        self.assertContains(page, "Колонка «Інформація»")
        self.assertContains(page, "Юридичні посилання")
        self.assertContains(page, "Кнопка дзвінка")
        self.assertContains(page, "Циліндри")
        self.assertContains(page, "Замовити дзвінок")
        self.assertNotContains(page, "Підвал — про нас (заголовок)")

    def test_frontend_renders_seeded_links(self):
        with translation.override("ua"):
            page = self.client.get("/ua/")
        body = page.content.decode()
        self.assertIn("site-footer__col", body)
        self.assertIn("Про нас", body)
        self.assertIn("/ua/info/about/", body)
        self.assertIn("Доставка та оплата", body)
        self.assertIn("/ua/info/delivery/", body)
        self.assertIn("Політика конфіденційності", body)
        footer = body[body.index('id="footer"') : body.index("</footer>")]
        self.assertLess(footer.index("Про нас"), footer.index("Доставка та оплата"))
        self.assertIn("data-open-callback", body)
        self.assertIn("Замовити дзвінок", body)

    def test_hidden_catalog_link_not_in_footer(self):
        FooterNavLink.objects.filter(key="cat-cyl").update(is_active=False)
        with translation.override("ua"):
            page = self.client.get("/ua/")
        footer = page.content.decode()
        start = footer.index('id="footer"')
        chunk = footer[start : footer.index("</footer>", start)]
        self.assertNotIn(">Циліндри</a>", chunk)

    def test_ru_callback_and_legal(self):
        rows = get_footer_nav("ru")
        self.assertEqual(rows["action"][0]["name"], "Заказать звонок")
        self.assertTrue(rows["action"][0]["is_callback"])
        privacy = next(item for item in rows["legal"] if item["key"] == "legal-privacy")
        self.assertTrue(privacy["href"].startswith("/ru/"))
        with translation.override("ru"):
            page = self.client.get("/ru/")
        self.assertContains(page, "Заказать звонок")
        self.assertContains(page, "Политика конфиденциальности")
        self.assertContains(page, "О нас")
        self.assertContains(page, "/ru/info/about/")

    def test_formset_hides_info_link(self):
        from pages.admin_footer_nav import build_footer_nav_formset

        fs = build_footer_nav_formset()
        data = {f"footer_nav-{k}": v for k, v in fs.management_form.initial.items()}
        forms = fs.initial_forms
        data["footer_nav-TOTAL_FORMS"] = str(len(forms))
        for i, form in enumerate(forms):
            inst = form.instance
            data[f"footer_nav-{i}-id"] = str(inst.pk)
            data[f"footer_nav-{i}-key"] = inst.key
            data[f"footer_nav-{i}-group"] = inst.group
            data[f"footer_nav-{i}-name"] = inst.name
            data[f"footer_nav-{i}-name_ru"] = inst.name_ru
            data[f"footer_nav-{i}-url"] = inst.url
            data[f"footer_nav-{i}-sort_order"] = str(inst.sort_order)
            if inst.key != "info-promos":
                data[f"footer_nav-{i}-is_active"] = "on"
        good = build_footer_nav_formset(data=data)
        self.assertTrue(good.is_valid(), good.errors)
        good.save()
        self.assertFalse(FooterNavLink.objects.get(key="info-promos").is_active)

    def test_ensure_adds_about_when_info_already_exists(self):
        FooterNavLink.objects.filter(key="info-about").delete()
        FooterNavLink.objects.filter(group=FooterNavLink.Group.INFO).update(
            sort_order=0
        )
        added = ensure_default_footer_nav()
        self.assertEqual(added, 1)
        about = FooterNavLink.objects.get(key="info-about")
        self.assertEqual(about.name, "Про нас")
        self.assertEqual(about.name_ru, "О нас")
        self.assertEqual(about.url, "/ua/info/about/")
        self.assertEqual(about.sort_order, 1)
        self.assertEqual(ensure_default_footer_nav(), 0)
