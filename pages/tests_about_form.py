from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from pages.models_cms import SiteBlock, SiteSettings, clear_site_blocks_cache
from pages.site_content_registry import build_content_sidebar_groups, get_section


class AboutFormCmsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "aboutform", "af@example.com", "pass12345"
        )
        SiteSettings.load()
        self.client = Client()
        self.client.force_login(self.user)

    def tearDown(self):
        translation.deactivate_all()

    def _admin(self):
        return reverse("admin:pages_aboutformsettings_change", args=[1])

    def test_sidebar_form_under_about(self):
        groups = build_content_sidebar_groups(admin_prefix="admin/")
        info = next(g for g in groups if g["title"] == "Інфосторінки")
        titles = [item["title"] for item in info["items"]]
        self.assertEqual(titles[:3], ["Про нас", "Форма", "Доставка і оплата"])
        section = get_section("about", "form")
        self.assertIsNotNone(section)
        self.assertFalse(section.include_style)

    def test_admin_shows_form_copy(self):
        page = self.client.get(self._admin())
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Залишилися питання?")
        self.assertContains(page, "Надіслати повідомлення")
        self.assertContains(page, "Або зателефонуйте:")
        self.assertContains(page, "Ім’я — підпис")
        self.assertContains(page, "Підбір замка або циліндра")
        self.assertContains(page, "Погоджуюсь з")
        self.assertContains(page, "Показувати секцію на сайті")
        self.assertContains(page, 'name="section_visible"')
        self.assertContains(page, "data-admin-lang")

    def test_frontend_uses_cms_title(self):
        self.client.get(self._admin())
        self.client.post(
            self._admin(),
            {
                "section_visible": "on",
                "block__about__about_form_title__text_html": "Питання з адмінки",
                "block__about__about_form_title__text_html_ru": "Вопросы из админки",
                "block__about__about_form_lead__text_html": "Лід форми",
                "block__about__about_form_lead__text_html_ru": "",
                "block__about__about_form_submit__text_html": "Надіслати зараз",
                "block__about__about_form_submit__text_html_ru": "",
                "block__about__about_form_or_call__text_html": "Або дзвоніть:",
                "block__about__about_form_or_call__text_html_ru": "",
            },
        )
        clear_site_blocks_cache()
        with translation.override("ua"):
            page = self.client.get("/ua/info/about/")
        self.assertContains(page, "Питання з адмінки")
        self.assertContains(page, "Лід форми")
        self.assertContains(page, "Надіслати зараз")
        self.assertContains(page, "Або дзвоніть:")
        with translation.override("ru"):
            ru = self.client.get("/ru/info/about/")
        self.assertContains(ru, "Вопросы из админки")

    def test_frontend_uses_cms_field_labels(self):
        self.client.get(self._admin())
        self.client.post(
            self._admin(),
            {
                "section_visible": "on",
                "block__about__about_form_name_label__text_html": "Ваше ім’я*",
                "block__about__about_form_name_label__text_html_ru": "Ваше имя*",
                "block__about__about_form_name_ph__text_html": "Марія",
                "block__about__about_form_name_ph__text_html_ru": "",
                "block__about__about_form_topic_lock__text_html": "Підібрати замок",
                "block__about__about_form_topic_lock__text_html_ru": "",
            },
        )
        clear_site_blocks_cache()
        with translation.override("ua"):
            page = self.client.get("/ua/info/about/")
        self.assertContains(page, "Ваше ім’я*")
        self.assertContains(page, "Марія")
        self.assertContains(page, "Підібрати замок")
        with translation.override("ru"):
            ru = self.client.get("/ru/info/about/")
        self.assertContains(ru, "Ваше имя*")

    def test_hidden_form_not_on_page(self):
        SiteBlock.objects.update_or_create(
            page="about",
            key="about_form_visible",
            defaults={"label": "v", "content_type": "text", "text_html": "0"},
        )
        clear_site_blocks_cache()
        with translation.override("ua"):
            page = self.client.get("/ua/info/about/")
        self.assertNotContains(page, "info-form-card")
        self.assertNotContains(page, "Залишилися питання?")
