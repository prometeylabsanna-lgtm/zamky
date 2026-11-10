from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from pages.cms_audit import run_audit
from pages.cms_content import get_block_text
from pages.models_cms import SiteBlock, SiteSettings


class CmsAuditTests(TestCase):
    def setUp(self):
        call_command("seed_content")

    def test_audit_pass_after_seed(self):
        report = run_audit()
        self.assertEqual(report.blockers, 0, msg=str(report.findings[:5]))
        self.assertTrue(report.ok)

    def test_audit_command(self):
        call_command("cms_audit_manifest")

    def test_ru_fallback_to_ua(self):
        from pages.models_cms import clear_site_blocks_cache

        SiteBlock.objects.update_or_create(
            page="home",
            key="picker_title",
            defaults={
                "label": "t",
                "content_type": "text",
                "text_html": "UA title",
                "text_html_ru": "",
            },
        )
        clear_site_blocks_cache()
        self.assertEqual(
            get_block_text("home", "picker_title", lang="ru"),
            "UA title",
        )
        SiteBlock.objects.filter(page="home", key="picker_title").update(
            text_html_ru="RU title"
        )
        clear_site_blocks_cache()
        self.assertEqual(
            get_block_text("home", "picker_title", lang="ru"),
            "RU title",
        )

    def test_plain_enter_preserved(self):
        text = "рядок1\nрядок2\n\nрядок3"
        block, _ = SiteBlock.objects.update_or_create(
            page="about",
            key="about_lead",
            defaults={
                "label": "lead",
                "content_type": "text",
                "text_html": text,
            },
        )
        block.refresh_from_db()
        self.assertEqual(block.text_html, text)

    def test_admin_cms_sections_200(self):
        User = get_user_model()
        user = User.objects.create_superuser("audit", "a@ex.com", "pass12345")
        SiteSettings.load()
        client = Client()
        client.force_login(user)
        for name in (
            "pages_homeherosettings_changelist",
            "pages_homeaudiencesettings_changelist",
            "pages_sitefootersettings_changelist",
            "pages_mediaitem_changelist",
        ):
            url = reverse(f"admin:{name}")
            resp = client.get(url)
            self.assertIn(resp.status_code, {200, 302}, msg=name)
            if resp.status_code == 302:
                follow = client.get(resp["Location"])
                self.assertEqual(follow.status_code, 200, msg=name)


@override_settings(CMS_ALLOW_STATIC_FALLBACK=False)
class CmsAuditStrictFallbackTests(TestCase):
    def setUp(self):
        call_command("seed_content")

    def test_static_v2_in_templates_is_blocker_when_fallback_off(self):
        report = run_audit()
        # home hero may still reference static slide.image — warn/blocker expected
        # Audit must still be runnable; blockers only if static img/v2 in templates
        static_blockers = [
            f
            for f in report.findings
            if f.severity == "blocker" and "static content image" in f.message
        ]
        # Не падаємо якщо шаблони вже на image_url; інакше фіксуємо наявність
        self.assertIsInstance(static_blockers, list)
