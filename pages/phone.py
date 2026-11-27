"""Телефон/email/графік з SiteSettings — одне джерело для вітрини."""

DEFAULT_PHONE_DISPLAY = "(067) 000 00 00"
DEFAULT_PHONE_TEL = "+380670000000"
DEFAULT_EMAIL = "info@centerzamkiv.com.ua"
DEFAULT_HOURS = "Щоденно 8:00-21:00"


def normalize_ua_tel(value: str) -> str:
    raw = (value or "").strip()
    if raw.lower().startswith("tel:"):
        raw = raw[4:].strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("380") and len(digits) >= 12:
        digits = digits[:12]
    elif digits.startswith("0") and len(digits) == 10:
        digits = "38" + digits
    elif digits.startswith("80") and len(digits) == 11:
        digits = "3" + digits
    elif len(digits) == 9:
        digits = "380" + digits
    return f"+{digits}"


def translate_ru(text: str) -> str:
    """UA-рядок через tr() за активної російської мови (словник RU_MAP)."""
    if not text:
        return text
    from django.utils.translation import override

    from pages.i18n_lib import tr

    with override("ru"):
        return tr(text)


def _is_ru(lang: str) -> bool:
    return str(lang or "").lower()[:2] == "ru"


def contacts_from_settings(site_settings, lang: str = "ua") -> dict[str, str]:
    if site_settings is None:
        phone = DEFAULT_PHONE_DISPLAY
        tel = DEFAULT_PHONE_TEL
        email = DEFAULT_EMAIL
        hours_ua = DEFAULT_HOURS
        hours_ru = ""
        address_ua = ""
        address_ru = ""
    else:
        phone = (site_settings.phone or "").strip() or DEFAULT_PHONE_DISPLAY
        tel = (
            normalize_ua_tel(site_settings.phone)
            or normalize_ua_tel(site_settings.phone_raw)
            or DEFAULT_PHONE_TEL
        )
        email = (site_settings.email or "").strip() or DEFAULT_EMAIL
        hours_ua = (site_settings.work_hours or "").strip() or DEFAULT_HOURS
        hours_ru = (site_settings.work_hours_ru or "").strip()
        address_ua = (site_settings.address or "").strip()
        address_ru = (site_settings.address_ru or "").strip()
    if _is_ru(lang):
        hours = hours_ru or translate_ru(hours_ua)
        address = address_ru or (translate_ru(address_ua) if address_ua else "")
    else:
        hours = hours_ua
        address = address_ua
    return {
        "phone": phone,
        "tel": tel,
        "email": email,
        "hours": hours,
        "address": address,
    }
