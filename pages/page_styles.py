"""Допоміжні функції стилів сторінок."""

from __future__ import annotations

import re

from django.core.cache import cache

from pages.models_cms import SiteBlock
from pages.models_page_style import PAGE_STYLES_CACHE_KEY, PageStyle, clear_page_styles_cache

_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

# (namespace, url_name) → PageStyle.page
_URL_PAGE_MAP: dict[tuple[str | None, str | None], str] = {
    ("catalog", "home"): SiteBlock.Page.HOME,
    ("catalog", "city"): SiteBlock.Page.HOME,
    ("catalog", "district"): SiteBlock.Page.HOME,
    ("catalog", "catalog"): SiteBlock.Page.CATALOG,
    ("catalog", "category"): SiteBlock.Page.CATALOG,
    ("catalog", "product"): SiteBlock.Page.PRODUCT,
    ("cart", "wishlist_page"): SiteBlock.Page.WISHLIST,
    ("cart", "drawer"): SiteBlock.Page.CART,
    ("orders", "checkout"): SiteBlock.Page.CHECKOUT,
    ("orders", "success"): SiteBlock.Page.CHECKOUT,
}

_INFO_SLUG_TO_PAGE = {
    "about": SiteBlock.Page.ABOUT,
    "delivery": SiteBlock.Page.DELIVERY,
    "warranty": SiteBlock.Page.WARRANTY,
    "returns": SiteBlock.Page.RETURNS,
    "install": SiteBlock.Page.INSTALL,
    "promos": SiteBlock.Page.PROMOS,
    "offer": SiteBlock.Page.OFFER,
    "privacy": SiteBlock.Page.PRIVACY,
    "blog": SiteBlock.Page.BLOG,
}


def normalize_hex(value: str, *, default: str = "") -> str:
    raw = (value or "").strip()
    if not raw:
        return default
    if not raw.startswith("#"):
        raw = f"#{raw}"
    if not _HEX_RE.match(raw):
        return default
    if len(raw) == 4:
        return f"#{raw[1] * 2}{raw[2] * 2}{raw[3] * 2}".lower()
    return raw.lower()


def clean_color(raw: str, *, default: str) -> str:
    """Повертає HEX або '' якщо збігається з дефолтом сайту."""
    value = normalize_hex(raw)
    if not value:
        return ""
    if value == normalize_hex(default) or value == default.lower():
        return ""
    return value


def ensure_all_page_styles() -> int:
    created = 0
    for value, _label in SiteBlock.Page.choices:
        _, was_created = PageStyle.objects.get_or_create(page=value)
        if was_created:
            created += 1
    if created:
        clear_page_styles_cache()
    return created


def resolve_page_key(request) -> str | None:
    match = getattr(request, "resolver_match", None)
    if match is None:
        return None
    url_name = match.url_name or ""
    namespace = match.namespace
    key = _URL_PAGE_MAP.get((namespace, url_name))
    if key:
        return key
    # cart app may have namespace
    if url_name == "wishlist_page":
        return SiteBlock.Page.WISHLIST
    if url_name in {"checkout", "success"}:
        return SiteBlock.Page.CHECKOUT
    if url_name == "drawer":
        return SiteBlock.Page.CART
    if url_name in {"info", "info_page"}:
        raw = (match.kwargs or {}).get("page", "about")
        return _INFO_SLUG_TO_PAGE.get(str(raw), SiteBlock.Page.ABOUT)
    if url_name == "blog_list":
        return SiteBlock.Page.BLOG
    return None


def _styles_map() -> dict[str, dict[str, str]]:
    cached = cache.get(PAGE_STYLES_CACHE_KEY)
    if cached is not None:
        return cached
    data: dict[str, dict[str, str]] = {}
    for row in PageStyle.objects.all():
        data[row.page] = {
            "bg": (row.background_color or "").strip(),
            "text": (row.text_color or "").strip(),
            "accent": (row.accent_color or "").strip(),
        }
    cache.set(PAGE_STYLES_CACHE_KEY, data, 300)
    return data


def get_page_style_vars(request) -> dict[str, str]:
    page = resolve_page_key(request)
    if not page:
        return {"bg": "", "text": "", "accent": ""}
    row = _styles_map().get(page, {})
    return {
        "bg": row.get("bg", ""),
        "text": row.get("text", ""),
        "accent": row.get("accent", ""),
    }
