from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from pages.legal_body import plain_text_to_html, sanitize_legal_html
from pages.models_cms import SiteBlock, SiteSettings, clear_site_blocks_cache
from pages.models_extra import BlogPost
from pages.site_content_registry import build_content_sidebar_groups, get_section


class BlogAdminCmsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "blogadmin", "blog@example.com", "pass12345"
        )
        SiteSettings.load()
        self.post = BlogPost.objects.create(
            title="Як вибрати замок для вхідних дверей?",
            excerpt="Клас захисту, тип механізму та сумісність з дверима",
            body=plain_text_to_html(
                "Для квартири рекомендуємо 3 клас.\n\n"
                "Циліндрові замки зручні при втраті ключів."
            ),
            is_published=True,
            sort_order=1,
        )
        self.client = Client()
        self.client.force_login(self.user)

    def tearDown(self):
        clear_site_blocks_cache()
        translation.deactivate_all()

    def test_sidebar_nested_under_info(self):
        groups = build_content_sidebar_groups(admin_prefix="admin/")
        info = next(g for g in groups if g["title"] == "Інфосторінки")
        titles = [item["title"] for item in info["items"]]
        self.assertIn("Корисне для вибору", titles)
        blog = next(i for i in info["items"] if i["title"] == "Корисне для вибору")
        nested = [sub["title"] for sub in blog.get("items", [])]
        self.assertEqual(nested, ["Список статей", "Маєте питання?"])
        self.assertIn("/admin/pages/blogpost/", blog["items"][0]["link"])
        self.assertIn("/admin/pages/blogasksettings/", blog["items"][1]["link"])
        self.assertNotIn("Маєте питання?", titles)
        ask = get_section("blog", "ask")
        self.assertIsNotNone(ask)
        self.assertTrue(ask.hide_from_sidebar)
        self.assertFalse(ask.include_style)

    def test_blog_not_in_leads_sidebar(self):
        from django.conf import settings

        nav = settings.UNFOLD["SIDEBAR"]["navigation"]
        leads = next(g for g in nav if g.get("title") == "Заявки")
        titles = [item["title"] for item in leads["items"]]
        self.assertNotIn("Блог", titles)
        self.assertNotIn("Список статей", titles)

    def test_admin_uses_tinymce(self):
        url = reverse("admin:pages_blogpost_change", args=[self.post.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "cms-tinymce")
        self.assertContains(page, "Текст статті")

    def test_admin_cover_fallback_preview(self):
        url = reverse("admin:pages_blogpost_change", args=[self.post.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "data-admin-img-preview")
        self.assertContains(page, "img/v2/")
        self.assertContains(page, "js/admin/image_preview.js")
        listing = self.client.get(reverse("admin:pages_blogpost_changelist"))
        self.assertContains(listing, "img/v2/")

    def test_article_renders_paragraphs(self):
        with translation.override("ua"):
            page = self.client.get(
                reverse("pages:blog_detail", kwargs={"slug": self.post.slug})
            )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "blog-prose")
        self.assertContains(page, "blog-cover")
        self.assertContains(page, "blog-aside")
        self.assertContains(page, "Покупцям")
        self.assertContains(page, "<p>", html=False)
        self.assertContains(page, "3 клас")
        article = page.content.decode().split('class="blog-prose"', 1)[1]
        self.assertNotIn("<script", article[:400])

    def test_ask_admin_fields(self):
        url = reverse("admin:pages_blogasksettings_change", args=[SiteSettings.load().pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Маєте питання?")
        self.assertContains(page, "Замовити дзвінок")
        self.assertContains(page, "Консультуємо щодня")

    def test_ask_cms_on_list(self):
        SiteBlock.objects.update_or_create(
            page="blog",
            key="blog_ask_title",
            defaults={
                "label": "Заголовок",
                "content_type": "text",
                "text_html": "Питання з адмінки?",
            },
        )
        SiteBlock.objects.update_or_create(
            page="blog",
            key="blog_ask_cta",
            defaults={
                "label": "Текст кнопки",
                "content_type": "text",
                "text_html": "Передзвоніть зараз",
            },
        )
        clear_site_blocks_cache()
        with translation.override("ua"):
            page = self.client.get(reverse("pages:blog_list"))
        self.assertContains(page, "Питання з адмінки?")
        self.assertContains(page, "Передзвоніть зараз")
        self.assertContains(page, "data-open-callback")

    def test_ask_hidden(self):
        SiteBlock.objects.update_or_create(
            page="blog",
            key="blog_ask_visible",
            defaults={"label": "v", "content_type": "text", "text_html": "0"},
        )
        clear_site_blocks_cache()
        with translation.override("ua"):
            page = self.client.get(reverse("pages:blog_list"))
        self.assertNotContains(page, "blog-aside__ask")
        self.assertContains(page, "Покупцям")

    def test_list_uses_cards(self):
        with translation.override("ua"):
            page = self.client.get(reverse("pages:blog_list"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "blog-cards")
        self.assertContains(page, "blog-card__go")
        self.assertContains(page, self.post.title)
        self.assertContains(page, "Покупцям")
        self.assertContains(page, "Маєте питання?")

    def test_sanitize_on_save(self):
        url = reverse("admin:pages_blogpost_change", args=[self.post.pk])
        self.client.post(
            url,
            {
                "title": self.post.title,
                "excerpt": self.post.excerpt,
                "body": '<p>ok</p><script>alert(1)</script><h2>Розділ</h2>',
                "is_published": "on",
                "sort_order": "1",
            },
        )
        self.post.refresh_from_db()
        self.assertIn("<p>ok</p>", self.post.body)
        self.assertIn("<h2>Розділ</h2>", self.post.body)
        self.assertNotIn("script", self.post.body.lower())

    def test_plain_text_to_html(self):
        html = plain_text_to_html("Перший абзац.\n\nДругий абзац.")
        self.assertIn("<p>Перший абзац.</p>", html)
        self.assertIn("<p>Другий абзац.</p>", html)
        clean = sanitize_legal_html("<p>x</p><script>alert(1)</script>")
        self.assertIn("<p>x</p>", clean)
        self.assertNotIn("script", clean.lower())
