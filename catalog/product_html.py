"""HTML-опис товару для сторінки товару."""

from __future__ import annotations

import re

from pages.legal_body import plain_text_to_html

from catalog.chrome_cms import _lang

_TAGS = re.compile(r"<[^>]+>")


def product_description_html(product, request) -> str:
    lang = _lang(request)
    raw = (product.description or "").strip()
    if lang == "ru":
        ru = (getattr(product, "description_ru", None) or "").strip()
        if ru:
            raw = ru
    html = plain_text_to_html(raw)
    if not _TAGS.sub("", html).strip():
        return ""
    return html
