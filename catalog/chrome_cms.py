"""Тексти оболонки каталогу з SiteBlock."""

from __future__ import annotations

from pages.cms_content import get_block_text, get_site_blocks_map


def _lang(request) -> str:
    raw = (getattr(request, "LANGUAGE_CODE", None) or "ua")[:2].lower()
    if raw in {"uk", "ua"}:
        return "ua"
    if raw == "ru":
        return "ru"
    return "ua"


def catalog_chrome(request) -> dict:
    lang = _lang(request)
    blocks = get_site_blocks_map()
    g = lambda key: get_block_text(  # noqa: E731
        "catalog", key, lang=lang, site_blocks=blocks
    )
    return {
        "title": g("catalog_title"),
        "empty": g("catalog_empty"),
        "filters_title": g("catalog_filters_title"),
    }
