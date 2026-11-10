"""Збірка інфосторінок (warranty…blog) + consult."""

from __future__ import annotations

from pages.cms_content import get_block_text


def _t(page: str, key: str, lang: str, blocks) -> str:
    return get_block_text(page, key, lang=lang, site_blocks=blocks)


def assemble_warranty(lang: str, blocks) -> dict:
    p = "warranty"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    return {
        "h1": g("warranty_title"),
        "lead": g("warranty_lead"),
        "layout": "blocks",
        "blocks": [
            {
                "type": "cards",
                "items": [
                    {
                        "value": g("warranty_card_1_value"),
                        "title": g("warranty_card_1_title"),
                        "text": g("warranty_card_1_text"),
                    },
                    {
                        "value": g("warranty_card_2_value"),
                        "title": g("warranty_card_2_title"),
                        "text": g("warranty_card_2_text"),
                    },
                    {
                        "value": g("warranty_card_3_value"),
                        "title": g("warranty_card_3_title"),
                        "text": g("warranty_card_3_text"),
                    },
                ],
            },
            {
                "type": "steps",
                "title": g("warranty_steps_title"),
                "items": [
                    {"title": g("warranty_step_1_title"), "text": g("warranty_step_1_text")},
                    {"title": g("warranty_step_2_title"), "text": g("warranty_step_2_text")},
                    {"title": g("warranty_step_3_title"), "text": g("warranty_step_3_text")},
                    {"title": g("warranty_step_4_title"), "text": g("warranty_step_4_text")},
                ],
            },
            {
                "type": "text",
                "title": g("warranty_exclude_title"),
                "bullets": [
                    g("warranty_exclude_1"),
                    g("warranty_exclude_2"),
                    g("warranty_exclude_3"),
                    g("warranty_exclude_4"),
                ],
            },
        ],
    }


def assemble_returns(lang: str, blocks) -> dict:
    p = "returns"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    return {
        "h1": g("returns_title"),
        "lead": g("returns_lead"),
        "layout": "blocks",
        "blocks": [
            {
                "type": "steps",
                "title": g("returns_steps_title"),
                "items": [
                    {"title": g("returns_step_1_title"), "text": g("returns_step_1_text")},
                    {"title": g("returns_step_2_title"), "text": g("returns_step_2_text")},
                    {"title": g("returns_step_3_title"), "text": g("returns_step_3_text")},
                    {"title": g("returns_step_4_title"), "text": g("returns_step_4_text")},
                ],
            },
            {
                "type": "text",
                "title": g("returns_terms_title"),
                "bullets": [
                    g("returns_terms_1"),
                    g("returns_terms_2"),
                    g("returns_terms_3"),
                ],
            },
            {
                "type": "text",
                "title": g("returns_no_title"),
                "paragraphs": [g("returns_no_body")],
            },
        ],
    }


def assemble_install(lang: str, blocks) -> dict:
    p = "install"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    prices = []
    for i in range(1, 8):
        prices.append((g(f"install_price_{i}_label"), g(f"install_price_{i}_value")))
    return {
        "h1": g("install_title"),
        "lead": g("install_lead"),
        "layout": "blocks",
        "blocks": [
            {
                "type": "cards",
                "items": [
                    {
                        "value": g("install_card_1_value"),
                        "title": g("install_card_1_title"),
                        "text": g("install_card_1_text"),
                    },
                    {
                        "value": g("install_card_2_value"),
                        "title": g("install_card_2_title"),
                        "text": g("install_card_2_text"),
                    },
                    {
                        "value": g("install_card_3_value"),
                        "title": g("install_card_3_title"),
                        "text": g("install_card_3_text"),
                    },
                ],
            },
            {"type": "table", "title": g("install_prices_title"), "rows": prices},
            {
                "type": "steps",
                "title": g("install_steps_title"),
                "items": [
                    {"title": g("install_step_1_title"), "text": g("install_step_1_text")},
                    {"title": g("install_step_2_title"), "text": g("install_step_2_text")},
                    {"title": g("install_step_3_title"), "text": g("install_step_3_text")},
                    {"title": g("install_step_4_title"), "text": g("install_step_4_text")},
                ],
            },
            {"type": "form", "title": g("install_form_title"), "form_key": "install"},
        ],
    }


def assemble_promos(lang: str, blocks) -> dict:
    p = "promos"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    items = []
    for i in range(1, 5):
        items.append(
            {
                "badge": g(f"promos_item_{i}_badge"),
                "title": g(f"promos_item_{i}_title"),
                "text": g(f"promos_item_{i}_text"),
                "until": g(f"promos_item_{i}_until"),
            }
        )
    return {
        "h1": g("promos_title"),
        "lead": g("promos_lead"),
        "layout": "blocks",
        "blocks": [
            {"type": "promos", "items": items},
            {
                "type": "text",
                "title": g("promos_terms_title"),
                "bullets": [
                    g("promos_terms_1"),
                    g("promos_terms_2"),
                    g("promos_terms_3"),
                ],
            },
        ],
    }


def assemble_offer(lang: str, blocks) -> dict:
    p = "offer"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    sections = []
    counts = {1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 0}
    for i in range(1, 7):
        paras = [g(f"offer_sec_{i}_p{j}") for j in range(1, counts[i] + 1)]
        sections.append((g(f"offer_sec_{i}_title"), paras))
    return {
        "h1": g("offer_title"),
        "rev": g("offer_rev"),
        "intro": g("offer_intro"),
        "sections": sections,
        "legal_box": g("offer_legal_box"),
    }


def assemble_privacy(lang: str, blocks) -> dict:
    p = "privacy"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    return {
        "h1": g("privacy_title"),
        "rev": g("privacy_rev"),
        "intro": g("privacy_intro"),
        "collect_title": g("privacy_collect_title"),
        "collect": [
            g("privacy_collect_1"),
            g("privacy_collect_2"),
            g("privacy_collect_3"),
        ],
        "why_title": g("privacy_why_title"),
        "why": g("privacy_why"),
        "who_title": g("privacy_who_title"),
        "who": g("privacy_who"),
        "rights_title": g("privacy_rights_title"),
        "rights": g("privacy_rights"),
        "callout": g("privacy_callout"),
    }


def assemble_blog(lang: str, blocks) -> dict:
    p = "blog"
    g = lambda k: _t(p, k, lang, blocks)  # noqa: E731
    return {
        "h1": g("blog_title"),
        "lead": g("blog_lead"),
        "layout": "blocks",
        "blocks": [{"type": "posts"}],
    }


def consult_context(lang: str, blocks) -> dict:
    g = lambda k: _t("site", k, lang, blocks)  # noqa: E731
    return {
        "hint": g("info_consult_hint"),
        "phone": g("info_consult_phone"),
        "hours": g("info_consult_hours"),
        "cta": g("info_consult_cta"),
    }
