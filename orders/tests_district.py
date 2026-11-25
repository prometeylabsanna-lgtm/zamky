from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from orders.models import DeliveryDistrict
from pages.models_cms import SiteSettings
from pages.site_content_registry import build_content_sidebar_groups


class DistrictOthersTitleTests(TestCase):
    def setUp(self):
        self.obolon = DeliveryDistrict.objects.create(
            slug="obolon",
            name="Оболонський",
            short="Оболонь",
            name_locative="Оболонському",
            others_title="Інші райони Києва",
            others_title_ru="Другие районы Киева",
            is_active=True,
            sort_order=0,
        )
        DeliveryDistrict.objects.create(
            slug="pechersk",
            name="Печерський",
            short="Печерськ",
            is_active=True,
            sort_order=1,
        )
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "distadmin", "dist@example.com", "pass12345"
        )
        SiteSettings.load()
        self.client = Client()
        self.client.force_login(self.user)

    def tearDown(self):
        translation.deactivate_all()

    def test_admin_has_others_title(self):
        url = reverse("admin:orders_deliverydistrict_change", args=[self.obolon.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Заголовок інших районів")
        self.assertContains(page, "Інші райони Києва")

    def test_cms_district_page_removed(self):
        groups = build_content_sidebar_groups(admin_prefix="admin/")
        home = next(g for g in groups if g["title"] == "Головна")
        titles = [item["title"] for item in home["items"]]
        self.assertNotIn("Район SEO", titles)

    def test_district_page_shows_title(self):
        self.obolon.others_title = "Сусідні райони"
        self.obolon.save(update_fields=["others_title"])
        with translation.override("ua"):
            page = self.client.get("/ua/kyiv/obolon/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Сусідні райони")
        self.assertContains(page, "Печерський")

    def test_ru_heading(self):
        self.assertEqual(self.obolon.others_heading("ru"), "Другие районы Киева")
        with translation.override("ru"):
            page = self.client.get("/ru/kyiv/obolon/")
        self.assertContains(page, "Другие районы Киева")
