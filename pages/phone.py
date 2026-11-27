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


def contacts_from_settings(site_settings, lang: str = "ua") -> dict[str, str]:
    if site_settings is None:
        return {
            "phone": DEFAULT_PHONE_DISPLAY,
            "tel": DEFAULT_PHONE_TEL,
            "email": DEFAULT_EMAIL,
            "hours": DEFAULT_HOURS,
        }
    phone = (site_settings.phone or "").strip() or DEFAULT_PHONE_DISPLAY
    tel = (
        normalize_ua_tel(site_settings.phone)
        or normalize_ua_tel(site_settings.phone_raw)
        or DEFAULT_PHONE_TEL
    )
    email = (site_settings.email or "").strip() or DEFAULT_EMAIL
    hours = (site_settings.work_hours or "").strip()
    if str(lang).lower()[:2] == "ru":
        hours_ru = (site_settings.work_hours_ru or "").strip()
        if hours_ru:
            hours = hours_ru
    if not hours:
        hours = DEFAULT_HOURS
    return {"phone": phone, "tel": tel, "email": email, "hours": hours}
