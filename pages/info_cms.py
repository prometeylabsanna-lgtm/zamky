"""Збірка інфосторінок з SiteBlock (формат як у info_content)."""

from __future__ import annotations

from pages.cms_content import get_block_text, get_site_blocks_map, is_section_visible
from pages.info_cms_2 import assemble_blog, assemble_blog_ask, assemble_install
from pages.info_cms_2 import assemble_offer, assemble_privacy, assemble_promos
from pages.info_cms_2 import assemble_returns, assemble_warranty, consult_context
from pages.phone import load_contacts, plaque_value


def _t(page: str, key: str, lang: str, blocks) -> str:
    return get_block_text(page, key, lang=lang, site_blocks=blocks)


def assemble_about(lang: str, blocks) -> dict:
    p = "about"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    contacts = load_contacts(lang)
    return {
        "h1": g("about_title"),
        "lead": g("about_lead"),
        "cards": [
            {"title": g("about_card_1_title"), "text": g("about_card_1_text")},
            {"title": g("about_card_2_title"), "text": g("about_card_2_text")},
            {"title": g("about_card_3_title"), "text": g("about_card_3_text")},
        ],
        "how_title": g("about_how_title"),
        "how_body": g("about_how_body"),
        "bullets": [g("about_bullet_1"), g("about_bullet_2"), g("about_bullet_3")],
        "shop_title": g("about_shop_title"),
        "rows": [
            (g("about_row_1_label"), plaque_value(blocks, p, "about_row_1_value", lang, contacts)),
            (g("about_row_2_label"), plaque_value(blocks, p, "about_row_2_value", lang, contacts)),
            (g("about_row_3_label"), plaque_value(blocks, p, "about_row_3_value", lang, contacts)),
            (g("about_row_4_label"), plaque_value(blocks, p, "about_row_4_value", lang, contacts)),
        ],
    }


def _ship_cost(key: str, lang: str, fallback: str) -> str:
    from decimal import Decimal, InvalidOperation

    from orders.utils import format_uah

    raw = (_t("checkout", key, lang, None) or fallback).replace(" ", "").replace(",", ".")
    try:
        amount = Decimal(raw)
    except (InvalidOperation, ValueError):
        amount = Decimal(fallback)
    if amount == 0:
        return _t("checkout", "ship_free", lang, None) or "Безкоштовно"
    return format_uah(amount)


def assemble_delivery(lang: str, blocks) -> dict:
    p = "delivery"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    np_cost = _ship_cost("ship_np_price", lang, "80")
    courier_cost = _ship_cost("ship_courier_price", lang, "150")
    pickup_cost = _ship_cost("ship_pickup_price", lang, "0")
    return {
        "h1": g("delivery_title"),
        "lead": g("delivery_lead"),
        "methods_title": g("delivery_methods_title"),
        "head": (g("delivery_head_1"), g("delivery_head_2"), g("delivery_head_3")),
        "rows": [
            (g("delivery_row_1_a"), g("delivery_row_1_b"), np_cost),
            (g("delivery_row_2_a"), g("delivery_row_2_b"), courier_cost),
            (g("delivery_row_3_a"), g("delivery_row_3_b"), pickup_cost),
        ],
        "note": g("delivery_note"),
        "pay_title": g("delivery_pay_title"),
        "pays": [
            (g("delivery_pay_1_title"), g("delivery_pay_1_text")),
            (g("delivery_pay_2_title"), g("delivery_pay_2_text")),
            (g("delivery_pay_3_title"), g("delivery_pay_3_text")),
        ],
        "return_title": g("delivery_return_title"),
        "return_body": g("delivery_return_body"),
        "steps": [g("delivery_step_1"), g("delivery_step_2"), g("delivery_step_3")],
    }


_ASSEMBLERS = {
    "about": assemble_about,
    "delivery": assemble_delivery,
    "warranty": assemble_warranty,
    "returns": assemble_returns,
    "install": assemble_install,
    "promos": assemble_promos,
    "offer": assemble_offer,
    "privacy": assemble_privacy,
    "blog": assemble_blog,
}


def for_page(key: str, *, lang: str = "ua", site_blocks=None) -> dict:
    blocks = site_blocks if site_blocks is not None else get_site_blocks_map()
    page = "about" if key == "contacts" else key
    fn = _ASSEMBLERS.get(page, assemble_about)
    return fn(lang, blocks)


def seo_for_page(key: str, *, lang: str = "ua", site_blocks=None) -> dict:
    blocks = site_blocks if site_blocks is not None else get_site_blocks_map()
    page = "about" if key == "contacts" else key
    if page not in _ASSEMBLERS:
        page = "about"
    return {
        "title": _t(page, f"{page}_seo_title", lang, blocks),
        "description": _t(page, f"{page}_seo_description", lang, blocks),
    }


def is_info_page_visible(page: str, *, site_blocks=None) -> bool:
    if page == "blog":
        return is_section_visible("blog", "blog_section_visible", site_blocks)
    return is_section_visible(page, f"{page}_section_visible", site_blocks)


def info_consult(lang: str = "ua", site_blocks=None) -> dict:
    blocks = site_blocks if site_blocks is not None else get_site_blocks_map()
    return consult_context(lang, blocks)


def blog_ask(lang: str = "ua", site_blocks=None) -> dict:
    blocks = site_blocks if site_blocks is not None else get_site_blocks_map()
    return assemble_blog_ask(lang, blocks)
