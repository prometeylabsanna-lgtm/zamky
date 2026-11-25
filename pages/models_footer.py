"""Посилання підвалу: каталог, інфо, юридичні, кнопка дзвінка."""

from __future__ import annotations

from django.db import models

from pages.models_cms import cta_url_validator


class FooterNavLink(models.Model):
    class Group(models.TextChoices):
        CATALOG = "catalog", "Каталог"
        INFO = "info", "Інформація"
        LEGAL = "legal", "Юридичні"
        ACTION = "action", "Дзвінок"

    key = models.SlugField("Код", max_length=40, unique=True)
    group = models.CharField(
        "Група",
        max_length=16,
        choices=Group.choices,
        default=Group.CATALOG,
        db_index=True,
    )
    name = models.CharField("Назва", max_length=80)
    name_ru = models.CharField("Назва (RU)", max_length=80, blank=True, default="")
    url = models.CharField(
        "Посилання",
        max_length=512,
        blank=True,
        default="",
        validators=[cta_url_validator],
        help_text="Наприклад /ua/info/delivery/. Порожнє в «Дзвінок» = модалка.",
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показувати", default=True)

    class Meta:
        verbose_name = "Посилання підвалу"
        verbose_name_plural = "Посилання підвалу"
        ordering = ["group", "sort_order", "pk"]

    def __str__(self) -> str:
        return f"{self.get_group_display()}: {self.name or self.key}"

    def display_name(self, lang: str = "ua") -> str:
        if lang == "ru" and self.name_ru.strip():
            return self.name_ru.strip()
        return self.name.strip()

    def is_callback(self) -> bool:
        if self.group != self.Group.ACTION:
            return False
        raw = (self.url or "").strip()
        return raw in {"", "#", "#callback"}
