"""HeroSlide: seed + frontend fallback на static."""

from __future__ import annotations

from dataclasses import dataclass

from pages.models_cms import HeroSlide

DEFAULT_HERO_SLIDES = (
    {
        "alt_text": "Акція Центр замків",
        "alt_text_ru": "Акция Центр замков",
        "link_url": "/ua/catalog/",
        "static_fallback": "img/v2/banner1.png",
        "sort_order": 0,
    },
    {
        "alt_text": "Акція Центр замків",
        "alt_text_ru": "Акция Центр замков",
        "link_url": "/ua/catalog/",
        "static_fallback": "img/v2/banner2.png",
        "sort_order": 1,
    },
    {
        "alt_text": "Акція Центр замків",
        "alt_text_ru": "Акция Центр замков",
        "link_url": "/ua/catalog/",
        "static_fallback": "img/v2/banner3.png",
        "sort_order": 2,
    },
    {
        "alt_text": "Акція Центр замків",
        "alt_text_ru": "Акция Центр замков",
        "link_url": "/ua/catalog/",
        "static_fallback": "img/v2/banner4.png",
        "sort_order": 3,
    },
)


@dataclass
class HeroSlideView:
    alt: str
    url: str
    image: str
    image_url: str | None


def _pick(lang: str, ua: str, ru: str) -> str:
    if lang == "ru" and (ru or "").strip():
        return ru
    return ua or ""


def ensure_default_hero_slides() -> int:
    if HeroSlide.objects.exists():
        return 0
    created = 0
    for item in DEFAULT_HERO_SLIDES:
        HeroSlide.objects.create(
            alt_text=item["alt_text"],
            alt_text_ru=item.get("alt_text_ru", ""),
            link_url=item["link_url"],
            static_fallback=item["static_fallback"],
            sort_order=item["sort_order"],
            is_active=True,
        )
        created += 1
    return created


def _allow_static_fallback() -> bool:
    from django.conf import settings

    return bool(getattr(settings, "CMS_ALLOW_STATIC_FALLBACK", True))


def get_hero_slides(lang: str = "ua") -> list[HeroSlideView]:
    # Lazy seed лише якщо дозволений static fallback (dev/demo).
    if _allow_static_fallback():
        ensure_default_hero_slides()
    rows = list(HeroSlide.objects.filter(is_active=True).order_by("sort_order", "pk"))
    allow_static = _allow_static_fallback()
    if not rows:
        if not allow_static:
            return []
        return [
            HeroSlideView(
                alt=item["alt_text"],
                url=item["link_url"],
                image=item["static_fallback"],
                image_url=None,
            )
            for item in DEFAULT_HERO_SLIDES
        ]
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
            )
        )
    return result
