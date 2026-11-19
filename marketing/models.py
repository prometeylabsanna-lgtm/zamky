"""Маркетинг: товарні фіди, SEO-налаштування, пікселі/лічильники.

Каталог (Product/Category) — зона DB: тут лише читаємо, схему каталогу не змінюємо.
"""

from __future__ import annotations

import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from marketing import validators as v


def _random_feed_slug() -> str:
    return f"feed-{secrets.token_hex(8)}"


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ProductFeed(models.Model):
    class FeedType(models.TextChoices):
        GOOGLE = "google", "Google Merchant (RSS 2.0, g:)"
        FACEBOOK = "facebook", "Facebook / Meta Catalog (RSS 2.0, g:)"
        PROM = "prom", "Prom.ua (YML)"

    class Currency(models.TextChoices):
        UAH = "UAH", "UAH"
        USD = "USD", "USD"
        EUR = "EUR", "EUR"

    name = models.CharField("Назва фіду (для адмінки)", max_length=120)
    feed_type = models.CharField("Тип", max_length=16, choices=FeedType.choices)
    slug = models.SlugField(
        "Слаг URL",
        max_length=64,
        unique=True,
        default=_random_feed_slug,
        help_text="Публічна адреса: /feeds/<слаг>.xml. Випадковий слаг ускладнює вгадування.",
    )
    is_enabled = models.BooleanField(
        "Увімкнено",
        default=False,
        help_text="Вимкнений фід віддає 404.",
    )
    access_token = models.CharField(
        "Токен доступу (необовʼязково)",
        max_length=64,
        blank=True,
        default="",
        help_text="Якщо заповнено, фід відкривається лише з ?token=… (порівняння compare_digest).",
    )
    shop_name = models.CharField("Назва магазину", max_length=120, blank=True, default="")
    company_name = models.CharField(
        "Компанія (для Prom)", max_length=200, blank=True, default=""
    )
    currency = models.CharField(
        "Валюта", max_length=3, choices=Currency.choices, default=Currency.UAH
    )
    only_in_stock = models.BooleanField("Лише в наявності", default=False)
    categories = models.ManyToManyField(
        "catalog.Category",
        verbose_name="Лише ці категорії",
        blank=True,
        related_name="+",
        help_text="Порожньо = увесь каталог. Підкатегорії обраних включаються.",
    )
    cache_hours = models.PositiveSmallIntegerField(
        "Кеш, годин",
        default=3,
        help_text="1–6. Кеш скидається при збереженні товару, категорії чи фіду.",
    )
    enabled_changed_at = models.DateTimeField(
        "Увімк./вимк. змінено", null=True, blank=True, editable=False
    )
    enabled_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Ким змінено увімк./вимк.",
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    last_generated_at = models.DateTimeField("Остання генерація", null=True, blank=True, editable=False)
    last_included = models.PositiveIntegerField("Товарів у фіді", default=0, editable=False)
    last_excluded = models.PositiveIntegerField("Виключено", default=0, editable=False)
    last_excluded_reasons = models.JSONField(
        "Причини виключення", default=dict, blank=True, editable=False
    )
    last_warnings = models.JSONField(
        "Попередження генерації", default=dict, blank=True, editable=False
    )
    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Товарний фід"
        verbose_name_plural = "Товарні фіди"
        ordering = ["feed_type", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.cache_hours < 1 or self.cache_hours > 6:
            raise ValidationError({"cache_hours": "Від 1 до 6 годин."})

    @property
    def public_path(self) -> str:
        return f"/feeds/{self.slug}.xml"


class FeedCategoryMapping(models.Model):
    feed = models.ForeignKey(
        ProductFeed, related_name="category_mappings", on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        "catalog.Category", verbose_name="Категорія сайту", on_delete=models.CASCADE, related_name="+"
    )
    google_product_category = models.PositiveIntegerField(
        "Google product category ID",
        help_text="Числовий ID з таксономії Google (напр. 2678 для замків).",
    )

    class Meta:
        verbose_name = "Мапінг категорії Google"
        verbose_name_plural = "Мапінг категорій Google"
        constraints = [
            models.UniqueConstraint(fields=["feed", "category"], name="uniq_feed_category_mapping")
        ]

    def __str__(self):
        return f"{self.category_id} → {self.google_product_category}"


class SeoSettings(SingletonModel):
    class OrgType(models.TextChoices):
        ORGANIZATION = "Organization", "Organization (без фізичної точки)"
        LOCAL_BUSINESS = "LocalBusiness", "LocalBusiness (є магазин / адреса)"

    primary_domain = models.CharField(
        "Основний домен",
        max_length=120,
        blank=True,
        default="",
        validators=[v.domain_validator],
        help_text="https://домен як на проді (з www або без). Порожньо = canonical/OG/JSON-LD не виводяться.",
    )
    title_default = models.CharField(
        "Title за замовчуванням (UA)",
        max_length=255,
        blank=True,
        default="",
        help_text="Для сторінок без власного title. Рекомендовано до 60 символів разом із суфіксом.",
    )
    title_default_ru = models.CharField(
        "Title за замовчуванням (RU)", max_length=255, blank=True, default=""
    )
    title_suffix = models.CharField(
        "Суфікс title (бренд)",
        max_length=60,
        blank=True,
        default="",
        help_text="Додається як « | Бренд». Не додається, якщо title вже містить бренд.",
    )
    description_default = models.CharField(
        "Description за замовчуванням (UA)",
        max_length=300,
        blank=True,
        default="",
        help_text="Рекомендовано 70–160 символів.",
    )
    description_default_ru = models.CharField(
        "Description за замовчуванням (RU)", max_length=300, blank=True, default=""
    )
    og_image = models.ImageField(
        "OG-картинка",
        upload_to="seo/",
        blank=True,
        null=True,
        validators=[v.validate_og_image_min],
        help_text="Рекомендовано 1200×630 px.",
    )
    og_image_alt = models.CharField("Alt OG-картинки", max_length=125, blank=True, default="")
    twitter_card = models.CharField(
        "twitter:card",
        max_length=32,
        default="summary_large_image",
        choices=[("summary_large_image", "summary_large_image"), ("summary", "summary")],
    )
    twitter_site = models.CharField(
        "twitter:site (handle)",
        max_length=16,
        blank=True,
        default="",
        validators=[v.twitter_handle_validator],
    )
    global_noindex = models.BooleanField(
        "Закрити ВЕСЬ сайт від індексації (noindex)",
        default=False,
        help_text="УВАГА: увімкнення прибирає весь сайт з Google. Лише для staging/демо.",
    )
    robots_extra = models.TextField(
        "Додаткові рядки robots.txt",
        blank=True,
        default="",
        validators=[v.validate_robots_extra],
        help_text="Додаються після автоматичних (Disallow: /admin/, Sitemap). Автоматичні не затираються.",
    )
    google_verification = models.CharField(
        "Google Search Console (content)", max_length=128, blank=True, default="",
        validators=[v.verification_validator],
    )
    bing_verification = models.CharField(
        "Bing Webmaster (content)", max_length=128, blank=True, default="",
        validators=[v.verification_validator],
    )
    meta_domain_verification = models.CharField(
        "Meta / Facebook domain (content)", max_length=128, blank=True, default="",
        validators=[v.verification_validator],
    )
    pinterest_verification = models.CharField(
        "Pinterest (content)", max_length=128, blank=True, default="",
        validators=[v.verification_validator],
    )
    org_type = models.CharField(
        "Тип організації (JSON-LD)",
        max_length=32,
        choices=OrgType.choices,
        default=OrgType.ORGANIZATION,
    )
    org_name = models.CharField(
        "Назва організації", max_length=200, blank=True, default="",
        help_text="Порожньо = «Назва сайту» з налаштувань.",
    )
    org_logo = models.ImageField(
        "Логотип для JSON-LD",
        upload_to="seo/",
        blank=True,
        null=True,
        validators=[v.validate_logo_min],
        help_text="Мінімум 112×112 px. Порожньо = логотип з налаштувань сайту (якщо ≥112×112).",
    )
    same_as = models.TextField(
        "sameAs (соцмережі)",
        blank=True,
        default="",
        validators=[v.validate_same_as],
        help_text="По одному https:// на рядок. Instagram/Telegram/Facebook з налаштувань додаються автоматично.",
    )
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "SEO-налаштування"
        verbose_name_plural = "SEO-налаштування"

    def __str__(self):
        return "SEO-налаштування"


class TrackingSettings(SingletonModel):
    ga4_enabled = models.BooleanField("GA4 увімкнено", default=False)
    ga4_id = models.CharField(
        "GA4 Measurement ID", max_length=24, blank=True, default="",
        validators=[v.ga4_validator], help_text="G-XXXXXXXXXX",
    )
    gtm_enabled = models.BooleanField("GTM увімкнено", default=False)
    gtm_id = models.CharField(
        "Google Tag Manager ID", max_length=24, blank=True, default="",
        validators=[v.gtm_validator], help_text="GTM-XXXXXXX",
    )
    google_ads_enabled = models.BooleanField("Google Ads увімкнено", default=False)
    google_ads_id = models.CharField(
        "Google Ads ID", max_length=24, blank=True, default="",
        validators=[v.google_ads_validator], help_text="AW-123456789",
    )
    meta_pixel_enabled = models.BooleanField("Meta Pixel увімкнено", default=False)
    meta_pixel_id = models.CharField(
        "Meta Pixel ID", max_length=24, blank=True, default="",
        validators=[v.meta_pixel_validator], help_text="Лише цифри",
    )
    tiktok_enabled = models.BooleanField("TikTok Pixel увімкнено", default=False)
    tiktok_pixel_id = models.CharField(
        "TikTok Pixel ID", max_length=40, blank=True, default="",
        validators=[v.tiktok_pixel_validator], help_text="Напр. C4ABCDEFGHIJ1234567",
    )
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    PAIRS = (
        ("ga4_enabled", "ga4_id"),
        ("gtm_enabled", "gtm_id"),
        ("google_ads_enabled", "google_ads_id"),
        ("meta_pixel_enabled", "meta_pixel_id"),
        ("tiktok_enabled", "tiktok_pixel_id"),
    )

    class Meta:
        verbose_name = "Пікселі та лічильники"
        verbose_name_plural = "Пікселі та лічильники"

    def __str__(self):
        return "Пікселі та лічильники"

    def clean(self):
        errors = {}
        for flag, field in self.PAIRS:
            if getattr(self, flag) and not (getattr(self, field) or "").strip():
                errors[field] = "Щоб увімкнути, вкажіть ID."
        if errors:
            raise ValidationError(errors)

    def active(self, flag: str, field: str) -> str:
        """ID лише якщо увімкнено і ID валідний (flag ≠ permission: потрібні обидва)."""
        value = (getattr(self, field) or "").strip()
        if not getattr(self, flag) or not value:
            return ""
        try:
            for validator in self._meta.get_field(field).validators:
                validator(value)
        except ValidationError:
            return ""
        return value
