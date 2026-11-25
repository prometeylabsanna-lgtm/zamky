"""Дефолти та payload посилань підвалу."""

from __future__ import annotations

from django.db.models import Case, F, IntegerField, Value, When

from pages.header_nav import _catalog_q, localize_href
from pages.models_footer import FooterNavLink

GROUP_WEIGHT = {
    FooterNavLink.Group.CATALOG: 0,
    FooterNavLink.Group.INFO: 1,
    FooterNavLink.Group.LEGAL: 2,
    FooterNavLink.Group.ACTION: 3,
}

FOOTER_NAV_GROUPS: tuple[tuple[str, str], ...] = (
    (FooterNavLink.Group.CATALOG, "Колонка «Каталог»"),
    (FooterNavLink.Group.INFO, "Колонка «Інформація»"),
    (FooterNavLink.Group.LEGAL, "Юридичні посилання"),
    (FooterNavLink.Group.ACTION, "Кнопка дзвінка"),
)

DEFAULT_FOOTER_NAV: tuple[dict[str, object], ...] = (
    {
        "key": "cat-cyl",
        "group": FooterNavLink.Group.CATALOG,
        "name": "Серцевини (циліндри)",
        "name_ru": "Сердцевины (цилиндры)",
        "url": _catalog_q("Серцевини (циліндри)"),
        "sort_order": 0,
    },
    {
        "key": "cat-locks",
        "group": FooterNavLink.Group.CATALOG,
        "name": "Замки",
        "name_ru": "Замки",
        "url": _catalog_q("Замки"),
        "sort_order": 1,
    },
    {
        "key": "cat-high-security",
        "group": FooterNavLink.Group.CATALOG,
        "name": "Замки підвищеного захисту",
        "name_ru": "Замки повышенной защиты",
        "url": _catalog_q("Замки підвищеного захисту"),
        "sort_order": 2,
    },
    {
        "key": "cat-mottura",
        "group": FooterNavLink.Group.CATALOG,
        "name": "Mottura",
        "name_ru": "Mottura",
        "url": _catalog_q("Mottura"),
        "sort_order": 3,
    },
    {
        "key": "cat-cisa",
        "group": FooterNavLink.Group.CATALOG,
        "name": "Cisa",
        "name_ru": "Cisa",
        "url": _catalog_q("Cisa"),
        "sort_order": 4,
    },
    {
        "key": "cat-elbor",
        "group": FooterNavLink.Group.CATALOG,
        "name": "Elbor",
        "name_ru": "Elbor",
        "url": _catalog_q("Elbor"),
        "sort_order": 5,
    },
    {
        "key": "info-about",
        "group": FooterNavLink.Group.INFO,
        "name": "Про нас",
        "name_ru": "О нас",
        "url": "/ua/info/about/",
        "sort_order": 0,
    },
    {
        "key": "info-delivery",
        "group": FooterNavLink.Group.INFO,
        "name": "Доставка та оплата",
        "name_ru": "Доставка и оплата",
        "url": "/ua/info/delivery/",
        "sort_order": 1,
    },
    {
        "key": "info-warranty",
        "group": FooterNavLink.Group.INFO,
        "name": "Гарантія",
        "name_ru": "Гарантия",
        "url": "/ua/info/warranty/",
        "sort_order": 2,
    },
    {
        "key": "info-returns",
        "group": FooterNavLink.Group.INFO,
        "name": "Обмін та повернення",
        "name_ru": "Обмен и возврат",
        "url": "/ua/info/returns/",
        "sort_order": 3,
    },
    {
        "key": "info-install",
        "group": FooterNavLink.Group.INFO,
        "name": "Установка",
        "name_ru": "Установка",
        "url": "/ua/info/install/",
        "sort_order": 4,
    },
    {
        "key": "info-promos",
        "group": FooterNavLink.Group.INFO,
        "name": "Акції",
        "name_ru": "Акции",
        "url": "/ua/info/promos/",
        "sort_order": 5,
    },
    {
        "key": "info-blog",
        "group": FooterNavLink.Group.INFO,
        "name": "Корисне для вибору",
        "name_ru": "Полезное для выбора",
        "url": "/ua/info/blog/",
        "sort_order": 6,
    },
    {
        "key": "legal-privacy",
        "group": FooterNavLink.Group.LEGAL,
        "name": "Політика конфіденційності",
        "name_ru": "Политика конфиденциальности",
        "url": "/ua/info/privacy/",
        "sort_order": 0,
    },
    {
        "key": "legal-offer",
        "group": FooterNavLink.Group.LEGAL,
        "name": "Публічна оферта",
        "name_ru": "Публичная оферта",
        "url": "/ua/info/offer/",
        "sort_order": 1,
    },
    {
        "key": "action-callback",
        "group": FooterNavLink.Group.ACTION,
        "name": "Замовити дзвінок",
        "name_ru": "Заказать звонок",
        "url": "",
        "sort_order": 0,
    },
)


def footer_nav_queryset():
    return FooterNavLink.objects.annotate(
        group_weight=Case(
            *[When(group=key, then=Value(weight)) for key, weight in GROUP_WEIGHT.items()],
            default=Value(9),
            output_field=IntegerField(),
        )
    ).order_by("group_weight", "sort_order", "pk")


def _create_footer_link(item: dict[str, object]) -> FooterNavLink:
    return FooterNavLink.objects.create(
        key=item["key"],
        group=item["group"],
        name=item["name"],
        name_ru=item["name_ru"],
        url=item["url"],
        sort_order=item["sort_order"],
        is_active=True,
    )


def _ensure_info_about_link() -> int:
    if FooterNavLink.objects.filter(key="info-about").exists():
        return 0
    spec = next(item for item in DEFAULT_FOOTER_NAV if item["key"] == "info-about")
    FooterNavLink.objects.filter(group=FooterNavLink.Group.INFO).update(
        sort_order=F("sort_order") + 1
    )
    _create_footer_link({**spec, "sort_order": 0})
    return 1


def ensure_default_footer_nav() -> int:
    if FooterNavLink.objects.exists():
        return _ensure_info_about_link()
    created = 0
    for item in DEFAULT_FOOTER_NAV:
        _create_footer_link(item)
        created += 1
    return created


def get_footer_nav(lang: str = "ua") -> dict[str, list[dict[str, str | bool]]]:
    ensure_default_footer_nav()
    code = "ru" if lang == "ru" else "ua"
    grouped: dict[str, list[dict[str, str | bool]]] = {
        key: [] for key, _ in FOOTER_NAV_GROUPS
    }
    for item in footer_nav_queryset().filter(is_active=True):
        grouped.setdefault(item.group, []).append(
            {
                "key": item.key,
                "name": item.display_name(code),
                "href": localize_href(item.url, code) if not item.is_callback() else "",
                "is_callback": item.is_callback(),
            }
        )
    return grouped
