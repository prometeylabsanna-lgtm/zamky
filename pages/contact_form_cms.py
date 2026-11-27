"""Тексти форми зворотного зв’язку з SiteBlock."""

from __future__ import annotations

from pages.cms_content import get_block_text, get_site_blocks_map

TOPIC_KEYS: tuple[tuple[str, str], ...] = (
    ("lock", "about_form_topic_lock"),
    ("order", "about_form_topic_order"),
    ("delivery", "about_form_topic_delivery"),
    ("return", "about_form_topic_return"),
    ("install", "about_form_topic_install"),
    ("other", "about_form_topic_other"),
)


def _lang(raw: str | None) -> str:
    code = (raw or "ua").lower()[:2]
    if code in {"uk", "ua"}:
        return "ua"
    if code == "ru":
        return "ru"
    return "ua"


def get_contact_form_copy(lang: str | None = "ua", site_blocks=None) -> dict:
    blocks = site_blocks if site_blocks is not None else get_site_blocks_map()
    code = _lang(lang)

    def g(key: str, fallback: str = "") -> str:
        return get_block_text(
            "about",
            key,
            lang=code,
            site_blocks=blocks,
            fallback=fallback,
        )

    return {
        "name_label": g("about_form_name_label", "Ім’я*"),
        "name_ph": g("about_form_name_ph", "Олександр"),
        "phone_label": g("about_form_phone_label", "Телефон*"),
        "phone_ph": g("about_form_phone_ph", "+38 (0__) ___ __ __"),
        "email_label": g("about_form_email_label", "Email"),
        "email_ph": g("about_form_email_ph", ""),
        "topic_label": g("about_form_topic_label", "Тема"),
        "topics": [(value, g(key)) for value, key in TOPIC_KEYS],
        "message_label": g("about_form_message_label", "Повідомлення*"),
        "message_ph": g(
            "about_form_message_ph",
            "Опишіть ваше питання. Для підбору вкажіть товщину дверей або розміри A і B.",
        ),
        "consent": g("about_form_consent", "Погоджуюсь з"),
        "consent_link": g(
            "about_form_consent_link", "політикою конфіденційності"
        ),
        "err_required": g(
            "about_form_err_required", "Поле обовʼязкове для заповнення"
        ),
    }
