"""Валідатори маркетингових полів (ID трекерів, verification, домен, посилання)."""

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.core.files.images import get_image_dimensions
from django.utils.deconstruct import deconstructible

GA4_RE = r"^G-[A-Z0-9]{4,16}$"
GTM_RE = r"^GTM-[A-Z0-9]{4,12}$"
META_PIXEL_RE = r"^[0-9]{6,20}$"
TIKTOK_PIXEL_RE = r"^[A-Z0-9]{10,32}$"
GOOGLE_ADS_RE = r"^AW-[0-9]{6,15}$"
VERIFICATION_RE = r"^[A-Za-z0-9_-]+$"
TWITTER_HANDLE_RE = r"^@?[A-Za-z0-9_]{1,15}$"
DOMAIN_RE = r"^https://[a-z0-9.-]+\.[a-z]{2,}$"

ga4_validator = RegexValidator(GA4_RE, "Формат GA4: G-XXXXXXXXXX (великі літери/цифри).")
gtm_validator = RegexValidator(GTM_RE, "Формат GTM: GTM-XXXXXXX.")
meta_pixel_validator = RegexValidator(META_PIXEL_RE, "Meta Pixel ID — лише цифри (6–20).")
tiktok_pixel_validator = RegexValidator(
    TIKTOK_PIXEL_RE, "TikTok Pixel ID — великі латинські літери та цифри (10–32)."
)
google_ads_validator = RegexValidator(GOOGLE_ADS_RE, "Формат Google Ads: AW-123456789.")
verification_validator = RegexValidator(
    VERIFICATION_RE,
    "Лише значення content: латиниця, цифри, _ і -. Без тегу <meta> і лапок.",
)
twitter_handle_validator = RegexValidator(
    TWITTER_HANDLE_RE, "Handle X/Twitter: @name (до 15 символів)."
)
domain_validator = RegexValidator(
    DOMAIN_RE,
    "Лише https://домен без шляху і слеша в кінці, напр. https://zamky.com.ua",
)


@deconstructible
class MinImageSizeValidator:
    def __init__(self, min_w: int, min_h: int):
        self.min_w = min_w
        self.min_h = min_h

    def __call__(self, file):
        if not file:
            return
        try:
            w, h = get_image_dimensions(file)
        except Exception:
            w, h = None, None
        if not w or not h:
            raise ValidationError("Не вдалося прочитати розмір зображення.")
        if w < self.min_w or h < self.min_h:
            raise ValidationError(
                f"Мінімум {self.min_w}×{self.min_h} px, завантажено {w}×{h} px."
            )

    def __eq__(self, other):
        return isinstance(other, MinImageSizeValidator) and (self.min_w, self.min_h) == (other.min_w, other.min_h)


validate_logo_min = MinImageSizeValidator(112, 112)
validate_og_image_min = MinImageSizeValidator(600, 315)


def validate_same_as(value: str):
    for line in (value or "").splitlines():
        line = line.strip()
        if line and not line.startswith("https://"):
            raise ValidationError(f"Кожен рядок — посилання https://…, помилка: {line[:80]}")


ROBOTS_DIRECTIVES = ("user-agent:", "allow:", "disallow:", "crawl-delay:", "sitemap:", "#")


def validate_robots_extra(value: str):
    for line in (value or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if not line.lower().startswith(ROBOTS_DIRECTIVES):
            raise ValidationError(
                "Дозволені рядки: User-agent:, Allow:, Disallow:, Crawl-delay:, Sitemap:, # коментар."
            )
        if "<" in line or ">" in line:
            raise ValidationError("У robots.txt не можна HTML.")
