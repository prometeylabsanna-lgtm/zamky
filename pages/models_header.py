"""Кнопки навігації в шапці."""

from __future__ import annotations

from django.db import models

from pages.models_cms import cta_url_validator


class HeaderNavLink(models.Model):
    key = models.SlugField("Код", max_length=40, unique=True)
    name = models.CharField("Назва", max_length=80)
    name_ru = models.CharField("Назва (RU)", max_length=80, blank=True, default="")
    url = models.CharField(
        "Посилання",
        max_length=512,
        blank=True,
        default="",
        validators=[cta_url_validator],
        help_text="Наприклад /ua/catalog/?q=Замки або /ua/info/promos/",
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показувати", default=True)
    in_header = models.BooleanField("Під пошуком", default=True)
    in_mobile = models.BooleanField("У меню телефону", default=False)

    class Meta:
        verbose_name = "Кнопка шапки"
        verbose_name_plural = "Кнопки шапки"
        ordering = ["sort_order", "pk"]

    def __str__(self) -> str:
        return self.name or self.key

    def display_name(self, lang: str = "ua") -> str:
        if lang == "ru" and self.name_ru.strip():
            return self.name_ru.strip()
        return self.name.strip()

    def save(self, *args, **kwargs):
        from catalog.filter_sort import apply_auto_sort_order

        apply_auto_sort_order(self, HeaderNavLink.objects.all())
        super().save(*args, **kwargs)
