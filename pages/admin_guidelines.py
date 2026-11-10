"""Підказки для CMS-форм."""

SECTION_HINTS: dict[tuple[str, str], str] = {
    ("home", "hero"): "Слайди банера: фото, alt, посилання. Порядок — drag у списку.",
    ("home", "audience"): "Чотири картки «для кого». Порожній RU = український текст.",
    ("site", "header"): "Підписи шапки та видимість іконок.",
    ("site", "footer"): "Тексти підвалу.",
}

KEY_HINTS: dict[str, str] = {
    "footer_copyright": "Рік можна оновлювати вручну.",
}


def help_for_section(page: str, slug: str) -> str:
    return SECTION_HINTS.get((page, slug), "")


def help_for_key(key: str, page: str = "") -> str:
    return KEY_HINTS.get(key, "")
