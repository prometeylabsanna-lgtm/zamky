"""CMS-моделі: SiteSettings, SiteBlock, HeroSlide."""

from django.core.cache import cache
from django.db import models

SITE_BLOCKS_CACHE_KEY = "zamky_site_blocks_v1"


class SiteSettings(models.Model):
    """Глобальні налаштування (singleton pk=1)."""

    site_name = models.CharField("Назва сайту", max_length=128, default="Замки")
    phone = models.CharField("Телефон", max_length=32, blank=True, default="")
    phone_raw = models.CharField(
        "Телефон для tel:",
        max_length=32,
        blank=True,
        default="",
        help_text="Лише цифри та +, для посилання tel:",
    )
    email = models.EmailField("Email", blank=True, default="")
    address = models.CharField("Адреса", max_length=255, blank=True, default="")
    address_ru = models.CharField("Адреса (RU)", max_length=255, blank=True, default="")
    work_hours = models.CharField("Графік", max_length=120, blank=True, default="")
    work_hours_ru = models.CharField("Графік (RU)", max_length=120, blank=True, default="")
    meta_title = models.CharField("SEO title (default)", max_length=200, blank=True, default="")
    meta_title_ru = models.CharField("SEO title RU", max_length=200, blank=True, default="")
    meta_description = models.CharField(
        "SEO description (default)", max_length=300, blank=True, default=""
    )
    meta_description_ru = models.CharField(
        "SEO description RU", max_length=300, blank=True, default=""
    )
    instagram_url = models.URLField("Instagram", blank=True, default="")
    telegram_url = models.URLField("Telegram", blank=True, default="")
    facebook_url = models.URLField("Facebook", blank=True, default="")
    logo = models.ImageField("Логотип", upload_to="brand/", blank=True, null=True)
    favicon = models.ImageField("Favicon", upload_to="brand/", blank=True, null=True)

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self):
        return self.site_name or "Налаштування сайту"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def load(cls):
        return cls.get_solo()


class SiteBlock(models.Model):
    """Один контент-ключ секції: текст / фото / url / visibility."""

    class Page(models.TextChoices):
        HOME = "home", "Головна"
        SITE = "site", "Сайт"
        ABOUT = "about", "Про нас"
        DELIVERY = "delivery", "Доставка"
        WARRANTY = "warranty", "Гарантія"
        RETURNS = "returns", "Обмін"
        INSTALL = "install", "Установка"
        PROMOS = "promos", "Акції"
        OFFER = "offer", "Оферта"
        PRIVACY = "privacy", "Політика"
        CATALOG = "catalog", "Каталог"
        PRODUCT = "product", "Товар"
        CART = "cart", "Кошик"
        CHECKOUT = "checkout", "Оформлення"
        WISHLIST = "wishlist", "Обране"

    class ContentType(models.TextChoices):
        TEXT = "text", "Текст"
        IMAGE = "image", "Фото"
        URL = "url", "Посилання"
        VIDEO = "video", "Відео"

    page = models.CharField("Сторінка", max_length=32, choices=Page.choices)
    key = models.CharField("Ключ", max_length=64)
    label = models.CharField("Підпис у адмінці", max_length=128, blank=True, default="")
    content_type = models.CharField(
        "Тип",
        max_length=16,
        choices=ContentType.choices,
        default=ContentType.TEXT,
    )
    text_html = models.TextField("Текст (UA)", blank=True, default="")
    text_html_ru = models.TextField("Текст (RU)", blank=True, default="")
    image = models.ImageField("Зображення", upload_to="blocks/", blank=True, null=True)
    media = models.ForeignKey(
        "pages.MediaItem",
        verbose_name="Медіатека",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="site_blocks",
    )
    link_url = models.CharField("URL посилання", max_length=512, blank=True, default="")
    link_label = models.CharField("Текст посилання (UA)", max_length=128, blank=True, default="")
    link_label_ru = models.CharField("Текст посилання (RU)", max_length=128, blank=True, default="")
    video_embed_url = models.URLField("Embed URL відео", blank=True, default="")
    video_file = models.FileField(
        "Файл відео", upload_to="blocks/video/", blank=True, null=True
    )
    sort_order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Блок контенту"
        verbose_name_plural = "Блоки контенту"
        constraints = [
            models.UniqueConstraint(
                fields=["page", "key"], name="unique_site_block_page_key"
            ),
        ]
        ordering = ["page", "sort_order", "key"]

    def __str__(self):
        return f"{self.page}.{self.key}"

    @property
    def cache_key(self) -> str:
        return f"{self.page}.{self.key}"


class HeroSlide(models.Model):
    """Слайд банера головної (CollectionMedia)."""

    image = models.ImageField("Зображення", upload_to="hero/", blank=True, null=True)
    media = models.ForeignKey(
        "pages.MediaItem",
        verbose_name="Медіатека",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="hero_slides",
    )
    alt_text = models.CharField("Alt (UA)", max_length=200, blank=True, default="")
    alt_text_ru = models.CharField("Alt (RU)", max_length=200, blank=True, default="")
    link_url = models.CharField("Посилання", max_length=512, blank=True, default="/catalog/")
    sort_order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активний", default=True)
    static_fallback = models.CharField(
        "Static fallback",
        max_length=255,
        blank=True,
        default="",
        help_text="Шлях у static/, якщо немає upload",
    )

    def resolved_image_url(self) -> str | None:
        if self.media_id and self.media and self.media.file:
            try:
                return self.media.file.url
            except Exception:
                pass
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        return None

    class Meta:
        verbose_name = "Слайд банера"
        verbose_name_plural = "Слайди банера"
        ordering = ["sort_order", "pk"]

    def __str__(self):
        return self.alt_text or f"Слайд {self.pk}"


def clear_site_blocks_cache() -> None:
    cache.delete(SITE_BLOCKS_CACHE_KEY)
