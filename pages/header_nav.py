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
        "in_header": True,
        "in_mobile": True,
    },
    {
        "key": "install",
        "name": "Установка",
        "name_ru": "Установка",
        "url": "/ua/info/install/",
        "sort_order": 8,
        "in_header": True,
        "in_mobile": True,
    },
    {
        "key": "wishlist",
        "name": "Обране",
        "name_ru": "Избранное",
        "url": "/ua/cart/wishlist/",
        "sort_order": 9,
        "in_header": False,
        "in_mobile": True,
    },
    {
        "key": "delivery",
        "name": "Доставка та оплата",
        "name_ru": "Доставка и оплата",
        "url": "/ua/info/delivery/",
        "sort_order": 10,
        "in_header": False,
        "in_mobile": True,
    },
    {
        "key": "warranty",
        "name": "Гарантія",
        "name_ru": "Гарантия",
        "url": "/ua/info/warranty/",
        "sort_order": 11,
        "in_header": False,
        "in_mobile": True,
    },
    {
        "key": "blog",
        "name": "Корисне для вибору",
        "name_ru": "Полезное для выбора",
        "url": "/ua/info/blog/",
        "sort_order": 12,
        "in_header": False,
        "in_mobile": True,
    },
    {
        "key": "offer",
        "name": "Публічна оферта",
        "name_ru": "Публичная оферта",
        "url": "/ua/info/offer/",
        "sort_order": 13,
        "in_header": False,
        "in_mobile": True,
    },
    {
        "key": "privacy",
        "name": "Політика конфіденційності",
        "name_ru": "Политика конфиденциальности",
        "url": "/ua/info/privacy/",
        "sort_order": 14,
        "in_header": False,
        "in_mobile": True,
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


def _place_columns_ready() -> bool:
    from django.db import connection

    table = HeaderNavLink._meta.db_table
    with connection.cursor() as cursor:
        names = {
            col.name
            for col in connection.introspection.get_table_description(cursor, table)
        }
    return "in_header" in names and "in_mobile" in names


def _raw_insert_link(item: dict[str, object]) -> None:
    from django.db import connection

    url = _nav_url(item)
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT id FROM {HeaderNavLink._meta.db_table} WHERE key = %s",
            [item["key"]],
        )
        if cursor.fetchone():
            return
        cursor.execute(
            f"""
            INSERT INTO {HeaderNavLink._meta.db_table}
                (key, name, name_ru, url, sort_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [item["key"], item["name"], item["name_ru"], url, item["sort_order"], True],
        )


def _create_header_link(item: dict[str, object]) -> bool:
    if not _place_columns_ready():
        _raw_insert_link(item)
        return False
    url = _nav_url(item)
    _obj, created = HeaderNavLink.objects.get_or_create(
        key=item["key"],
        defaults={
            "name": item["name"],
            "name_ru": item["name_ru"],
            "url": url,
            "sort_order": item["sort_order"],
            "is_active": True,
            "in_header": bool(item.get("in_header", True)),
            "in_mobile": bool(item.get("in_mobile", False)),
        },
    )
    return created


def sync_default_header_nav() -> int:
    keep = {item["key"] for item in DEFAULT_HEADER_NAV}
    if not _place_columns_ready():
        for item in DEFAULT_HEADER_NAV:
            _raw_insert_link(item)
        return len(DEFAULT_HEADER_NAV)
    for item in DEFAULT_HEADER_NAV:
        _create_header_link(item)
    HeaderNavLink.objects.exclude(key__in=keep).delete()
    return len(DEFAULT_HEADER_NAV)


def ensure_default_header_nav() -> int:
    created = 0
    for item in DEFAULT_HEADER_NAV:
        if _create_header_link(item):
            created += 1
    return created


def get_header_nav_links(lang: str = "ua", *, mobile: bool = False) -> list[dict[str, str]]:
    ensure_default_header_nav()
    code = "ru" if lang == "ru" else "ua"
    rows: list[dict[str, str]] = []
    qs = HeaderNavLink.objects.filter(is_active=True).order_by("sort_order", "pk")
    if mobile:
        qs = qs.filter(in_mobile=True)
    else:
        qs = qs.filter(in_header=True)
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
