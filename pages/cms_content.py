"""Хелпери читання CMS-блоків для вітрини (fallback RU→UA)."""

from __future__ import annotations

from django.core.cache import cache

from pages.block_defaults import get_block_default
from pages.models_cms import SITE_BLOCKS_CACHE_KEY, SiteBlock


def _lang_code(lang: str | None) -> str:
    code = (lang or "ua").lower()
    if code in {"uk", "ua", "ukrainian"}:
        return "ua"
    if code.startswith("ru"):
        return "ru"
    return "ua"


def get_site_blocks_map() -> dict[str, SiteBlock]:
    cached = cache.get(SITE_BLOCKS_CACHE_KEY)
    if cached is not None:
        return cached
    mapping = {f"{b.page}.{b.key}": b for b in SiteBlock.objects.filter(is_active=True)}
    cache.set(SITE_BLOCKS_CACHE_KEY, mapping, 60 * 10)
    return mapping


def get_block_text(
    page: str,
    key: str,
    *,
    lang: str = "ua",
    site_blocks: dict[str, SiteBlock] | None = None,
    fallback: str | None = None,
) -> str:
    blocks = site_blocks if site_blocks is not None else get_site_blocks_map()
    block = blocks.get(f"{page}.{key}")
    default = fallback if fallback is not None else get_block_default(page, key)
    if block is None:
        return default
    code = _lang_code(lang)
    ua = block.text_html or default
    if code == "ru":
        ru = (block.text_html_ru or "").strip()
        return ru if ru else ua
    return ua


def is_section_visible(
    page: str,
    visibility_key: str,
    site_blocks: dict[str, SiteBlock] | None = None,
) -> bool:
    value = get_block_text(
        page,
        visibility_key,
        site_blocks=site_blocks,
        fallback="1",
    )
    return value not in {"0", "false", "False", ""}
