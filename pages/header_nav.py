"""Дефолти та payload кнопок шапки."""

from __future__ import annotations

from pages.models_header import HeaderNavLink

_LANG_PREFIXES = ("/ua/", "/ru/")


def _catalog_q(query: str) -> str:
    return f"/ua/catalog/?q={query.replace(' ', '+')}"


def category_href(name: str) -> str:
    from catalog.models import Category

    cat = Category.objects.filter(
        name=name, parent__isnull=True, is_active=True
    ).first()
    if cat is not None:
        return cat.get_absolute_url()
    return "/ua/catalog/"


def _nav_url(item: dict[str, object]) -> str:
    category = str(item.get("category") or "").strip()
    if category:
        return category_href(category)
    return str(item.get("url") or "")


DEFAULT_HEADER_NAV: tuple[dict[str, object], ...] = (
    {
        "key": "locks",
        "name": "Замки",
        "name_ru": "Замки",
        "category": "Замки",
        "sort_order": 1,
    },
    {
        "key": "cyl",
        "name": "Циліндри",
        "name_ru": "Цилиндры",
        "category": "Циліндри",
        "sort_order": 2,
    },
    {
        "key": "hardware",
        "name": "Дверна фурнітура",
        "name_ru": "Дверная фурнитура",
        "category": "Дверна фурнітура",
        "sort_order": 3,
    },
    {
        "key": "plates",
        "name": "Броненакладки",
        "name_ru": "Броненакладки",
        "category": "Броненакладки",
        "sort_order": 4,
    },
    {
        "key": "closers",
        "name": "Дотягувачі",
        "name_ru": "Доводчики",
        "category": "Дотягувачі",
        "sort_order": 5,
    },
    {
        "key": "access",
        "name": "Контроль доступу",
        "name_ru": "Контроль доступа",
        "category": "Контроль доступу",
        "sort_order": 6,
    },
    {
        "key": "promos",
        "name": "Акції",
        "name_ru": "Акции",
        "url": "/ua/info/promos/",
        "sort_order": 7,
    },
    {
        "key": "install",
        "name": "Установка",
        "name_ru": "Установка",
        "url": "/ua/info/install/",
        "sort_order": 8,
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


def _write_header_link(item: dict[str, object]) -> HeaderNavLink:
    url = _nav_url(item)
    obj, _created = HeaderNavLink.objects.update_or_create(
        key=item["key"],
        defaults={
            "name": item["name"],
            "name_ru": item["name_ru"],
            "url": url,
            "sort_order": item["sort_order"],
            "is_active": True,
        },
    )
    return obj


def sync_default_header_nav() -> int:
    keep = {item["key"] for item in DEFAULT_HEADER_NAV}
    for item in DEFAULT_HEADER_NAV:
        _write_header_link(item)
    HeaderNavLink.objects.exclude(key__in=keep).delete()
    return len(DEFAULT_HEADER_NAV)


def ensure_default_header_nav() -> int:
    if HeaderNavLink.objects.exists():
        return 0
    return sync_default_header_nav()


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
