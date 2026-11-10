"""G7: seed ≡ admin counts."""

from __future__ import annotations

from dataclasses import dataclass

from pages.hero_slides import DEFAULT_HERO_SLIDES
from pages.models_cms import HeroSlide, SiteBlock, SiteSettings
from pages.site_content_registry import CONTENT_SECTIONS, all_registry_block_keys


@dataclass(frozen=True)
class ParityReport:
    site_settings: int
    site_blocks: int
    expected_blocks: int
    hero_slides: int
    expected_heroes: int
    sections: int
    missing_block_keys: tuple[tuple[str, str], ...]
    ok: bool


def collect_parity() -> ParityReport:
    expected_keys = all_registry_block_keys()
    existing = set(
        SiteBlock.objects.values_list("page", "key")
    )
    missing = tuple(k for k in expected_keys if k not in existing)
    settings_n = 1 if SiteSettings.objects.filter(pk=1).exists() else 0
    blocks_n = sum(1 for k in expected_keys if k in existing)
    heroes = HeroSlide.objects.filter(is_active=True).count()
    expected_heroes = len(DEFAULT_HERO_SLIDES)
    ok = (
        settings_n == 1
        and not missing
        and heroes >= expected_heroes
    )
    return ParityReport(
        site_settings=settings_n,
        site_blocks=blocks_n,
        expected_blocks=len(expected_keys),
        hero_slides=heroes,
        expected_heroes=expected_heroes,
        sections=len(CONTENT_SECTIONS),
        missing_block_keys=missing,
        ok=ok,
    )
