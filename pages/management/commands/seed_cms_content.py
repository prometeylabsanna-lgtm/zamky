"""Ідемпотентний seed CMS: SiteSettings + усі registry keys + hero slides."""

from django.core.management.base import BaseCommand, CommandError

from pages.block_defaults import (
    get_block_content_type,
    get_block_default,
    get_block_label,
)
from pages.hero_slides import ensure_default_hero_slides
from pages.models_cms import SiteBlock, SiteSettings, clear_site_blocks_cache
from pages.seed_parity import collect_parity
from pages.site_content_registry import all_registry_block_keys


class Command(BaseCommand):
    help = "Seed SiteSettings, SiteBlock keys, HeroSlide (без overwrite існуючого)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Лише перевірити seed ≡ registry (exit 1 якщо fail).",
        )

    def handle(self, *args, **options):
        if options["check"]:
            report = collect_parity()
            self._print_report(report)
            if not report.ok:
                raise CommandError("CMS seed parity FAIL")
            self.stdout.write(self.style.SUCCESS("CMS seed parity OK"))
            return

        settings_obj, created_settings = SiteSettings.objects.get_or_create(
            pk=1,
            defaults={
                "site_name": "Замки",
                "phone": "(067) 000 00 00",
                "phone_raw": "+380670000000",
                "email": "info@centrzamkiv.ua",
                "address": "м. Київ",
                "work_hours": "Щоденно 8:00-21:00",
                "work_hours_ru": "Ежедневно 8:00-21:00",
            },
        )
        if created_settings:
            self.stdout.write(self.style.SUCCESS("SiteSettings створено"))
        else:
            dirty = False
            for field, value in (
                ("phone", "(067) 000 00 00"),
                ("phone_raw", "+380670000000"),
                ("email", "info@centrzamkiv.ua"),
                ("address", "м. Київ"),
                ("work_hours", "Щоденно 8:00-21:00"),
            ):
                if not getattr(settings_obj, field):
                    setattr(settings_obj, field, value)
                    dirty = True
            if dirty:
                settings_obj.save()
                self.stdout.write("SiteSettings дозаповнено порожні контакти")
            else:
                self.stdout.write("SiteSettings вже є")

        created_blocks = 0
        filled_blocks = 0
        from pages.block_defaults_ru import get_block_default_ru

        for page, key in all_registry_block_keys():
            ua_default = get_block_default(page, key)
            ru_default = get_block_default_ru(page, key)
            defaults = {
                "label": get_block_label(page, key),
                "content_type": get_block_content_type(page, key),
                "text_html": ua_default,
                "text_html_ru": ru_default,
            }
            block, created = SiteBlock.objects.get_or_create(
                page=page, key=key, defaults=defaults
            )
            if created:
                created_blocks += 1
                continue
            dirty_fields: list[str] = []
            if not (block.label or "").strip():
                block.label = get_block_label(page, key)
                dirty_fields.append("label")
            # Залити поточні тексти сайту в порожні поля (не перезаписувати ручні правки).
            if ua_default and not (block.text_html or "").strip():
                block.text_html = ua_default
                dirty_fields.append("text_html")
            if ru_default and not (block.text_html_ru or "").strip():
                block.text_html_ru = ru_default
                dirty_fields.append("text_html_ru")
            if dirty_fields:
                block.save(update_fields=dirty_fields)
                filled_blocks += 1

        hero_created = ensure_default_hero_slides()
        from pages.page_styles import ensure_all_page_styles

        styles_created = ensure_all_page_styles()
        clear_site_blocks_cache()
        self.stdout.write(
            self.style.SUCCESS(
                f"SiteBlock +{created_blocks} filled {filled_blocks}, "
                f"HeroSlide +{hero_created}, PageStyle +{styles_created}"
            )
        )
        report = collect_parity()
        self._print_report(report)
        if not report.ok:
            raise CommandError("CMS seed parity FAIL після seed")

    def _print_report(self, report):
        self.stdout.write(
            f"parity: settings={report.site_settings} "
            f"blocks={report.site_blocks}/{report.expected_blocks} "
            f"heroes={report.hero_slides}/{report.expected_heroes} "
            f"sections={report.sections}"
        )
        if report.missing_block_keys:
            sample = ", ".join(f"{p}.{k}" for p, k in report.missing_block_keys[:8])
            self.stdout.write(self.style.WARNING(f"missing keys: {sample}"))
