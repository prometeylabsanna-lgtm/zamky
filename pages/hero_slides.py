"""HeroSlide: seed + frontend fallback на static."""

from __future__ import annotations

from dataclasses import dataclass, field

from pages.models_cms import HeroSlide

HERO_BRAND_LOGOS = (
    ("img/v2/hero/brands/wm.png", "WM"),
    ("img/v2/hero/brands/apex.png", "Apecs"),
    ("img/v2/hero/brands/cisa.png", "Cisa"),
    ("img/v2/hero/brands/mottura.png", "Mottura"),
    ("img/v2/hero/brands/elbor.png", "Elbor"),
    ("img/v2/hero/brands/kale.png", "Kale"),
)

HERO_FEATURES = (
    ("shield", "Оригінальна продукція"),
    ("people", "Професійна консультація"),
    ("box", "Швидка доставка"),
    ("tool", "Встановлення та сервіс"),
)

DEFAULT_HERO_SLIDES = (
    {
        "alt_text": "Замки, фурнітура, циліндри 24/7",
        "alt_text_ru": "Замки, фурнитура, цилиндры 24/7",
        "headline": "Замки, фурнітура, циліндри",
        "headline_ru": "Замки, фурнитура, цилиндры",
        "headline_accent": "24/7",
        "headline_accent_ru": "24/7",
        "subtitle": "Швидкий підбір. Офіційні бренди. Доставка та професійна установка",
        "subtitle_ru": "Быстрый подбор. Официальные бренды. Доставка и профессиональная установка",
        "link_url": "/ua/catalog/",
        "static_fallback": "img/v2/hero/slide-home.webp",
        "cta_primary_label": "Перейти до каталогу",
        "cta_primary_label_ru": "Перейти в каталог",
        "cta_primary_url": "/ua/catalog/",
        "cta_secondary_label": "Підібрати замок за 2 хв",
        "cta_secondary_label_ru": "Подобрать замок за 2 мин",
        "cta_secondary_url": "#picker",
        "show_secondary": True,
        "cta_primary_light": False,
        "show_features": True,
        "show_brands": False,
        "sort_order": 0,
    },
    {
        "alt_text": "Акції та спецпропозиції",
        "alt_text_ru": "Акции и спецпредложения",
        "headline": "Акції та спецпропозиції",
        "headline_ru": "Акции и спецпредложения",
        "headline_accent": "",
        "headline_accent_ru": "",
        "subtitle": "",
        "subtitle_ru": "",
        "link_url": "/ua/info/promos/",
        "static_fallback": "img/v2/hero/slide-promo.webp",
        "cta_primary_label": "Перейти до акцій",
        "cta_primary_label_ru": "Перейти к акциям",
        "cta_primary_url": "/ua/info/promos/",
        "cta_secondary_label": "",
        "cta_secondary_label_ru": "",
        "cta_secondary_url": "",
        "show_secondary": False,
        "cta_primary_light": True,
        "show_features": False,
        "show_brands": False,
        "sort_order": 1,
    },
    {
        "alt_text": "Професійна установка замків у Києві та області",
        "alt_text_ru": "Профессиональная установка замков в Киеве и области",
        "headline": "Професійна установка замків у Києві та області",
        "headline_ru": "Профессиональная установка замков в Киеве и области",
        "headline_accent": "",
        "headline_accent_ru": "",
        "subtitle": "",
        "subtitle_ru": "",
        "link_url": "/ua/info/install/",
        "static_fallback": "img/v2/hero/slide-install.webp",
        "cta_primary_label": "Замовити установку",
        "cta_primary_label_ru": "Заказать установку",
        "cta_primary_url": "/ua/info/install/",
        "cta_secondary_label": "",
        "cta_secondary_label_ru": "",
        "cta_secondary_url": "",
        "show_secondary": False,
        "cta_primary_light": False,
        "show_features": False,
        "show_brands": False,
        "sort_order": 2,
    },
    {
        "alt_text": "Оригінальні бренди",
        "alt_text_ru": "Оригинальные бренды",
        "headline": "Оригінальні бренди",
        "headline_ru": "Оригинальные бренды",
        "headline_accent": "",
        "headline_accent_ru": "",
        "subtitle": "",
        "subtitle_ru": "",
        "link_url": "/ua/catalog/",
        "static_fallback": "img/v2/hero/slide-brands.webp",
        "cta_primary_label": "Всі бренди",
        "cta_primary_label_ru": "Все бренды",
        "cta_primary_url": "/ua/catalog/",
        "cta_secondary_label": "",
        "cta_secondary_label_ru": "",
        "cta_secondary_url": "",
        "show_secondary": False,
        "cta_primary_light": True,
        "show_features": False,
        "show_brands": False,
        "sort_order": 3,
    },
)

_SLIDE_COPY_KEYS = (
    "alt_text",
    "alt_text_ru",
    "headline",
    "headline_ru",
    "headline_accent",
    "headline_accent_ru",
    "subtitle",
    "subtitle_ru",
    "link_url",
    "static_fallback",
    "cta_primary_label",
    "cta_primary_label_ru",
    "cta_primary_url",
    "cta_secondary_label",
    "cta_secondary_label_ru",
    "cta_secondary_url",
    "show_secondary",
    "cta_primary_light",
    "show_features",
    "show_brands",
    "sort_order",
)


@dataclass
class HeroSlideView:
    alt: str
    url: str
    image: str
    image_url: str | None
    cta_primary_label: str = ""
    cta_primary_url: str = ""
    cta_secondary_label: str = ""
    cta_secondary_url: str = ""
    headline: str = ""
    headline_accent: str = ""
    subtitle: str = ""
    show_secondary: bool = False
    cta_primary_light: bool = False
    show_features: bool = False
    show_brands: bool = False
    brands: tuple[tuple[str, str], ...] = field(default_factory=tuple)


def _pick(lang: str, ua: str, ru: str) -> str:
    if lang == "ru" and (ru or "").strip():
        return ru
    return ua or ""


def _slide_kwargs(item: dict) -> dict:
    return {key: item[key] for key in _SLIDE_COPY_KEYS}


def ensure_default_hero_slides() -> int:
    if HeroSlide.objects.exists():
        return 0
    created = 0
    for item in DEFAULT_HERO_SLIDES:
        HeroSlide.objects.create(**_slide_kwargs(item), is_active=True)
        created += 1
    return created


def apply_overlay_defaults(slide, item: dict) -> None:
    """Заповнює overlay-поля, не затираючи вже задані тексти кнопок."""
    for key in _SLIDE_COPY_KEYS:
        if key.startswith("cta_") and getattr(slide, key, ""):
            continue
        setattr(slide, key, item[key])


def _allow_static_fallback() -> bool:
    from django.conf import settings

    return bool(getattr(settings, "CMS_ALLOW_STATIC_FALLBACK", True))


def _view_from_item(item: dict, lang: str) -> HeroSlideView:
    return HeroSlideView(
        alt=_pick(lang, item["alt_text"], item.get("alt_text_ru", "")),
        url=item["link_url"],
        image=item["static_fallback"],
        image_url=None,
        cta_primary_label=_pick(
            lang, item.get("cta_primary_label", ""), item.get("cta_primary_label_ru", "")
        ),
        cta_primary_url=item.get("cta_primary_url", ""),
        cta_secondary_label=_pick(
            lang,
            item.get("cta_secondary_label", ""),
            item.get("cta_secondary_label_ru", ""),
        ),
        cta_secondary_url=item.get("cta_secondary_url", ""),
        headline=_pick(lang, item.get("headline", ""), item.get("headline_ru", "")),
        headline_accent=_pick(
            lang, item.get("headline_accent", ""), item.get("headline_accent_ru", "")
        ),
        subtitle=_pick(lang, item.get("subtitle", ""), item.get("subtitle_ru", "")),
        show_secondary=bool(item.get("show_secondary")),
        cta_primary_light=bool(item.get("cta_primary_light")),
        show_features=bool(item.get("show_features")),
        show_brands=bool(item.get("show_brands")),
        brands=HERO_BRAND_LOGOS if item.get("show_brands") else (),
    )


def get_hero_slides(lang: str = "ua") -> list[HeroSlideView]:
    if _allow_static_fallback():
        ensure_default_hero_slides()
    rows = list(HeroSlide.objects.filter(is_active=True).order_by("sort_order", "pk"))
    allow_static = _allow_static_fallback()
    if not rows:
        if not allow_static:
            return []
        return [_view_from_item(item, lang) for item in DEFAULT_HERO_SLIDES]
    result: list[HeroSlideView] = []
    for row in rows:
        image_url = row.resolved_image_url()
        static_image = row.static_fallback or "" if allow_static else ""
        alt = _pick(lang, row.alt_text, row.alt_text_ru)
        if row.media_id and row.media:
            alt = _pick(
                lang,
                row.media.alt_text or row.alt_text,
                row.media.alt_text_ru or row.alt_text_ru,
            )
        if not image_url and not static_image:
            continue
        result.append(
            HeroSlideView(
                alt=alt,
                url=row.link_url or "/ua/catalog/",
                image=static_image,
                image_url=image_url,
                cta_primary_label=_pick(
                    lang, row.cta_primary_label, row.cta_primary_label_ru
                ).strip(),
                cta_primary_url=(row.cta_primary_url or "").strip(),
                cta_secondary_label=_pick(
                    lang, row.cta_secondary_label, row.cta_secondary_label_ru
                ).strip(),
                cta_secondary_url=(row.cta_secondary_url or "").strip(),
                headline=_pick(lang, row.headline, row.headline_ru).strip(),
                headline_accent=_pick(
                    lang, row.headline_accent, row.headline_accent_ru
                ).strip(),
                subtitle=_pick(lang, row.subtitle, row.subtitle_ru).strip(),
                show_secondary=bool(row.show_secondary),
                cta_primary_light=bool(row.cta_primary_light),
                show_features=bool(row.show_features),
                show_brands=bool(row.show_brands),
                brands=HERO_BRAND_LOGOS if row.show_brands else (),
            )
        )
    return result
