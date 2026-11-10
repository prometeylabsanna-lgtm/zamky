"""Збірка інфосторінок з SiteBlock (формат як у info_content)."""

from __future__ import annotations

from pages.cms_content import get_block_text, get_site_blocks_map, is_section_visible
from pages.info_cms_2 import assemble_blog, assemble_install, assemble_offer
from pages.info_cms_2 import assemble_privacy, assemble_promos, assemble_returns
from pages.info_cms_2 import assemble_warranty, consult_context


def _t(page: str, key: str, lang: str, blocks) -> str:
    return get_block_text(page, key, lang=lang, site_blocks=blocks)


def assemble_about(lang: str, blocks) -> dict:
    p = "about"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
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
            (g("about_row_1_label"), g("about_row_1_value")),
            (g("about_row_2_label"), g("about_row_2_value")),
            (g("about_row_3_label"), g("about_row_3_value")),
            (g("about_row_4_label"), g("about_row_4_value")),
        ],
    }


def assemble_delivery(lang: str, blocks) -> dict:
    p = "delivery"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    return {
        "h1": g("delivery_title"),
        "lead": g("delivery_lead"),
        "methods_title": g("delivery_methods_title"),
        "head": (g("delivery_head_1"), g("delivery_head_2"), g("delivery_head_3")),
        "rows": [
            (g("delivery_row_1_a"), g("delivery_row_1_b"), g("delivery_row_1_c")),
            (g("delivery_row_2_a"), g("delivery_row_2_b"), g("delivery_row_2_c")),
            (g("delivery_row_3_a"), g("delivery_row_3_b"), g("delivery_row_3_c")),
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


def is_info_page_visible(page: str, *, site_blocks=None) -> bool:
    if page == "blog":
        return is_section_visible("blog", "blog_section_visible", site_blocks)
    return is_section_visible(page, f"{page}_section_visible", site_blocks)


def info_consult(lang: str = "ua", site_blocks=None) -> dict:
    blocks = site_blocks if site_blocks is not None else get_site_blocks_map()
    return consult_context(lang, blocks)
