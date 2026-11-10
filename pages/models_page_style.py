"""Стилі сторінок CMS: фон / шрифт / підсвітка."""

from django.core.cache import cache
from django.db import models

from pages.models_cms import SiteBlock, clear_site_blocks_cache

PAGE_STYLES_CACHE_KEY = "zamky_page_styles_v1"


def clear_page_styles_cache() -> None:
    cache.delete(PAGE_STYLES_CACHE_KEY)


class PageStyle(models.Model):
    """Кольори контенту сторінки. Порожні значення = поточний дизайн сайту."""

    DEFAULT_BACKGROUND = "#ffffff"
    DEFAULT_TEXT = "#505050"
    DEFAULT_ACCENT = "#f97f0c"

    page = models.CharField(
        "Сторінка",
        max_length=32,
        choices=SiteBlock.Page.choices,
        unique=True,
    )
    background_color = models.CharField(
        "Колір фону",
        max_length=32,
        blank=True,
        default="",
        help_text="HEX. Порожнє — як зараз на сайті.",
    )
    text_color = models.CharField(
        "Колір шрифту",
        max_length=32,
        blank=True,
        default="",
        help_text="HEX. Порожнє — як зараз на сайті.",
    )
    accent_color = models.CharField(
        "Колір підсвітки",
        max_length=32,
        blank=True,
        default="",
        help_text="HEX. Порожнє — як зараз на сайті.",
    )

    class Meta:
        ordering = ["page"]
        verbose_name = "Оформлення сторінки"
        verbose_name_plural = "Оформлення сторінок"

    def __str__(self) -> str:
        return f"Оформлення: {self.get_page_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        clear_page_styles_cache()
        clear_site_blocks_cache()

    def reset_to_default(self) -> None:
        self.background_color = ""
        self.text_color = ""
        self.accent_color = ""
        self.save(update_fields=["background_color", "text_color", "accent_color"])

    @classmethod
    def for_page(cls, page: str) -> "PageStyle":
        obj, _ = cls.objects.get_or_create(page=page)
        return obj

    @property
    def effective_background(self) -> str:
        return (self.background_color or "").strip() or self.DEFAULT_BACKGROUND

    @property
    def effective_text(self) -> str:
        return (self.text_color or "").strip() or self.DEFAULT_TEXT

    @property
    def effective_accent(self) -> str:
        return (self.accent_color or "").strip() or self.DEFAULT_ACCENT
