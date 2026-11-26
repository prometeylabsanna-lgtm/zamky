"""Хелпери читання CMS-блоків для вітрини (fallback RU→UA)."""

from __future__ import annotations

from config.cache_safe import cache_get, cache_set
from pages.block_defaults import STATIC_FALLBACKS, get_block_default
from pages.models_cms import SITE_BLOCKS_CACHE_KEY, SiteBlock


def _lang_code(lang: str | None) -> str:
    code = (lang or "ua").lower()
    if code in {"uk", "ua", "ukrainian"}:
        return "ua"
    if code.startswith("ru"):
        return "ru"
    return "ua"


def get_site_blocks_map() -> dict[str, SiteBlock]:
    cached = cache_get(SITE_BLOCKS_CACHE_KEY)
    if cached is not None:
        return cached
    mapping = {f"{b.page}.{b.key}": b for b in SiteBlock.objects.filter(is_active=True)}
    cache_set(SITE_BLOCKS_CACHE_KEY, mapping, 60 * 10)
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


def _safe_media_url(field_file) -> str:
    if not field_file or not getattr(field_file, "name", ""):
        return ""
    try:
        storage = getattr(field_file, "storage", None)
        name = field_file.name
        if storage is not None and hasattr(storage, "exists") and not storage.exists(name):
            return ""
        return field_file.url or ""
    except Exception:
        return ""


def get_block_image_url(
    page: str,
    key: str,
    *,
    site_blocks: dict[str, SiteBlock] | None = None,
) -> str:
    blocks = site_blocks if site_blocks is not None else get_site_blocks_map()
    block = blocks.get(f"{page}.{key}")
    if block is not None:
        if block.media_id and block.media:
            url = _safe_media_url(getattr(block.media, "file", None))
            if url:
                return url
        url = _safe_media_url(block.image)
        if url:
            return url
    static_path = STATIC_FALLBACKS.get((page, key), "")
    if not static_path:
        return ""
    from django.templatetags.static import static

    return static(static_path)


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
