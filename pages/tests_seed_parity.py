from django.core.management import call_command
from django.test import TestCase

from pages.hero_slides import DEFAULT_HERO_SLIDES
from pages.models_cms import HeroSlide, SiteBlock, SiteSettings
from pages.seed_parity import collect_parity
from pages.site_content_registry import all_registry_block_keys


class SeedParityTests(TestCase):
    def test_seed_creates_all_registry_keys(self):
        call_command("seed_content")
        report = collect_parity()
        self.assertTrue(report.ok, msg=str(report))
        self.assertEqual(report.site_settings, 1)
        self.assertEqual(report.site_blocks, report.expected_blocks)
        self.assertGreaterEqual(report.hero_slides, len(DEFAULT_HERO_SLIDES))
        self.assertEqual(SiteSettings.objects.filter(pk=1).count(), 1)
        self.assertEqual(
            SiteBlock.objects.filter(
                page__in={p for p, _ in all_registry_block_keys()}
            ).count(),
            len(all_registry_block_keys()),
        )

    def test_seed_idempotent(self):
        call_command("seed_cms_content")
        blocks_before = SiteBlock.objects.count()
        heroes_before = HeroSlide.objects.count()
        call_command("seed_cms_content")
        self.assertEqual(SiteBlock.objects.count(), blocks_before)
        self.assertEqual(HeroSlide.objects.count(), heroes_before)

    def test_seed_check_command(self):
        call_command("seed_content")
        call_command("seed_content", check=True)
