"""Збірка CMS-контексту для головної."""

from __future__ import annotations

from pages.cms_content import get_block_text, get_site_blocks_map, is_section_visible
from pages.hero_slides import get_hero_slides


def _lang_from_request(request) -> str:
    raw = getattr(request, "LANGUAGE_CODE", None) or "ua"
    code = str(raw).lower()[:2]
    if code in {"uk", "ua"}:
        return "ua"
    if code == "ru":
        return "ru"
    return "ua"


def build_home_cms(request) -> dict:
    lang = _lang_from_request(request)
    blocks = get_site_blocks_map()
    t = lambda page, key, fallback="": get_block_text(  # noqa: E731
        page, key, lang=lang, site_blocks=blocks, fallback=fallback
    )
    vis = lambda page, key: is_section_visible(page, key, site_blocks=blocks)  # noqa: E731

    audience = []
    icons = ("home", "biz", "tools", "shield")
    for i, icon in enumerate(icons, start=1):
        audience.append(
            {
                "title": t("home", f"audience_{i}_title"),
                "text": t("home", f"audience_{i}_text"),
                "icon": icon,
            }
        )

    category_subs = [t("home", f"categories_{i}_sub") for i in range(1, 7)]

    hero = []
    for slide in get_hero_slides(lang=lang):
        hero.append(
            {
                "alt": slide.alt,
                "url": slide.url,
                "image": slide.image,
                "image_url": slide.image_url,
            }
        )

    return {
        "site_blocks": blocks,
        "cms_lang": lang,
        "hero_slides": hero,
        "show_hero": vis("home", "hero_section_visible"),
        "audience": audience,
        "show_audience": vis("home", "audience_section_visible"),
        "show_categories": vis("home", "categories_section_visible"),
        "categories_title": t("home", "categories_title", "Категорії"),
        "category_subs": category_subs,
        "show_picker": vis("home", "picker_section_visible"),
        "picker_title": t("home", "picker_title"),
        "picker_lead": t("home", "picker_lead"),
        "picker_step1": t("home", "picker_step1"),
        "picker_step2": t("home", "picker_step2"),
        "picker_photo_text": t("home", "picker_photo_text"),
        "picker_photo_cta": t("home", "picker_photo_cta"),
        "picker_submit": t("home", "picker_submit", "Показати замки"),
        "show_popular": vis("home", "popular_section_visible"),
        "popular_title": t("home", "popular_title"),
        "popular_tab_hits": t("home", "popular_tab_hits"),
        "popular_tab_news": t("home", "popular_tab_news"),
        "popular_tab_sales": t("home", "popular_tab_sales"),
        "show_blog": vis("home", "blog_section_visible"),
        "blog_title": t("home", "blog_title"),
        "blog_more_label": t("home", "blog_more_label"),
        "show_district": vis("home", "district_section_visible"),
        "district_others_title": t("home", "district_others_title"),
    }
