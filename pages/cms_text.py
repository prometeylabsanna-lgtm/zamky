"""Короткі CMS-фрази для відповідей форм."""

from __future__ import annotations


def request_lang(request) -> str:
    lang = (getattr(request, "LANGUAGE_CODE", None) or "ua")[:2].lower()
    if lang in {"uk", "ua"}:
        return "ua"
    return "ru" if lang == "ru" else "ua"


def cms_text(page: str, key: str, lang: str, fallback: str = "", **tokens) -> str:
    from pages.cms_content import get_block_text

    text = get_block_text(page, key, lang=lang, fallback=fallback) or fallback
    for name, value in tokens.items():
        text = text.replace("{" + name + "}", "" if value is None else str(value))
    return text
