"""Політика index/noindex і hreflang без зміни видимого тексту."""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.utils.translation import get_language

TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
        "yclid",
        "msclkid",
        "_openstat",
    }
)

NOINDEX_ROUTES = frozenset(
    {
        ("catalog", "city"),
        ("catalog", "district"),
        ("catalog", "api_picker"),
        ("catalog", "api_search"),
        ("catalog", "product_review"),
        ("cart", "drawer"),
        ("cart", "badge"),
        ("cart", "add"),
        ("cart", "update"),
        ("cart", "wishlist_page"),
        ("cart", "wishlist"),
        ("orders", "checkout"),
        ("orders", "success"),
        ("orders", "set_district"),
        ("orders", "quick"),
        ("orders", "pay_wait"),
        ("orders", "pay_return"),
        ("orders", "pay_stub"),
        ("pages", "contact"),
        ("pages", "callback"),
        ("pages", "photo_pick"),
        ("pages", "install"),
    }
)
NOINDEX_URL_NAMES = frozenset({"set_lang"})
SKIP_CANONICAL_ROUTES = frozenset({("catalog", "city"), ("catalog", "district")})
CATALOG_LISTING = frozenset({("catalog", "catalog"), ("catalog", "category")})
HREFLANG_MAP = {"ua": "uk", "ru": "ru"}
LANG_PREFIX_RE = re.compile(r"^/(ua|uk|ru)(?=/|$)")


@dataclass(frozen=True)
class IndexPolicy:
    noindex: bool = False
    skip_canonical: bool = False


def route_of(request) -> tuple[str | None, str | None]:
    match = getattr(request, "resolver_match", None) if request is not None else None
    if match is None:
        return None, None
    return match.namespace, match.url_name


def is_search_request(request) -> bool:
    if route_of(request) not in CATALOG_LISTING:
        return False
    q = (request.GET.get("q") or "").strip()
    sku = (request.GET.get("sku") or "").strip()
    return bool(q or sku)


def has_index_noise_query(request) -> bool:
    if request is None:
        return False
    return bool(set(request.GET.keys()) - TRACKING_PARAMS)


def page_index_policy(request) -> IndexPolicy:
    if request is None:
        return IndexPolicy()
    ns, name = route_of(request)
    if name in NOINDEX_URL_NAMES or (ns, name) in NOINDEX_ROUTES:
        return IndexPolicy(
            noindex=True,
            skip_canonical=(ns, name) in SKIP_CANONICAL_ROUTES,
        )
    if is_search_request(request):
        return IndexPolicy(noindex=True, skip_canonical=True)
    if has_index_noise_query(request):
        return IndexPolicy(noindex=True, skip_canonical=False)
    return IndexPolicy()


def localized_path(path: str, lang: str) -> str:
    path = path or "/"
    swapped = LANG_PREFIX_RE.sub(f"/{lang}", path)
    if swapped != path:
        return swapped
    if path.startswith(f"/{lang}/") or path == f"/{lang}":
        return path
    if not path.startswith("/"):
        path = "/" + path
    return f"/{lang}{path}"


def hreflang_links(path: str, domain: str) -> list[dict[str, str]]:
    if not domain or not path:
        return []
    links = []
    for code, hreflang in HREFLANG_MAP.items():
        links.append(
            {
                "lang": hreflang,
                "href": f"{domain}{localized_path(path, code)}",
            }
        )
    links.append(
        {
            "lang": "x-default",
            "href": f"{domain}{localized_path(path, 'ua')}",
        }
    )
    return links


def current_lang_code() -> str:
    code = (get_language() or "ua")[:2].lower()
    return "ru" if code == "ru" else "ua"
