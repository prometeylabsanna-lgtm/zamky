"""Дефолти та payload кнопок шапки."""

from __future__ import annotations

from pages.models_header import HeaderNavLink

_LANG_PREFIXES = ("/ua/", "/ru/")


def _catalog_q(query: str) -> str:
    return f"/ua/catalog/?q={query.replace(' ', '+')}"


DEFAULT_HEADER_NAV: tuple[dict[str, object], ...] = (
    {
        "key": "cyl",
        "name": "Серцевини (циліндри)",
        "name_ru": "Сердцевины (цилиндры)",
        "url": _catalog_q("Серцевини (циліндри)"),
        "sort_order": 0,
    },
    {
        "key": "locks",
        "name": "Замки",
        "name_ru": "Замки",
        "url": _catalog_q("Замки"),
        "sort_order": 1,
    },
    {
        "key": "high-security",
        "name": "Замки підвищеного захисту",
        "name_ru": "Замки повышенной защиты",
        "url": _catalog_q("Замки підвищеного захисту"),
        "sort_order": 2,
    },
    {
        "key": "mottura",
        "name": "Mottura",
        "name_ru": "Mottura",
        "url": _catalog_q("Mottura"),
        "sort_order": 3,
    },
    {
        "key": "cisa",
        "name": "Cisa",
        "name_ru": "Cisa",
        "url": _catalog_q("Cisa"),
        "sort_order": 4,
    },
    {
        "key": "elbor",
        "name": "Elbor",
        "name_ru": "Elbor",
        "url": _catalog_q("Elbor"),
        "sort_order": 5,
    },
    {
        "key": "promos",
        "name": "Акції",
        "name_ru": "Акции",
        "url": "/ua/info/promos/",
        "sort_order": 6,
    },
    {
        "key": "install",
        "name": "Установка",
        "name_ru": "Установка",
        "url": "/ua/info/install/",
        "sort_order": 7,
    },
)


def localize_href(url: str, lang: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return "#"
    if raw.startswith(("http://", "https://", "tel:", "mailto:", "#")):
        return raw
    prefix = f"/{lang}/" if lang in {"ua", "ru"} else "/ua/"
    for item in _LANG_PREFIXES:
        if raw.startswith(item):
            return prefix + raw[len(item) :]
    if raw.startswith("/") and not raw.startswith("//"):
        return prefix + raw.lstrip("/")
    return raw


def nav_style(url: str, key: str = "") -> str:
    blob = f"{key} {url}".lower()
    if "promo" in blob:
        return "promo"
    if "install" in blob:
        return "install"
    return "link"


def ensure_default_header_nav() -> int:
    if HeaderNavLink.objects.exists():
        return 0
    created = 0
    for item in DEFAULT_HEADER_NAV:
        HeaderNavLink.objects.create(
            key=item["key"],
            name=item["name"],
            name_ru=item["name_ru"],
            url=item["url"],
            sort_order=item["sort_order"],
            is_active=True,
        )
        created += 1
    return created


def get_header_nav_links(lang: str = "ua") -> list[dict[str, str]]:
    ensure_default_header_nav()
    code = "ru" if lang == "ru" else "ua"
    rows: list[dict[str, str]] = []
    qs = HeaderNavLink.objects.filter(is_active=True).order_by("sort_order", "pk")
    for item in qs:
        rows.append(
            {
                "key": item.key,
                "name": item.display_name(code),
                "href": localize_href(item.url, code),
                "style": nav_style(item.url, item.key),
            }
        )
    return rows
