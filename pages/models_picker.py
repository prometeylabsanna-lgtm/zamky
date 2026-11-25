"""CMS підбору на головній: типи дверей і фільтри."""

from __future__ import annotations

from django.db import models


class PickerDoor(models.Model):
    code = models.SlugField("Код", max_length=40, unique=True)
    label_line1 = models.CharField("Рядок 1", max_length=40)
    label_line1_ru = models.CharField("Рядок 1 (RU)", max_length=40, blank=True, default="")
    label_line2 = models.CharField("Рядок 2", max_length=40, blank=True, default="")
    label_line2_ru = models.CharField("Рядок 2 (RU)", max_length=40, blank=True, default="")
    image = models.ImageField("Картинка", upload_to="picker/doors/", blank=True)
    static_fallback = models.CharField("Static fallback", max_length=255, blank=True, default="")
    match_hints = models.CharField(
        "Підказки категорій",
        max_length=180,
        blank=True,
        default="",
        help_text="Через кому: які категорії товарів підходять.",
    )
    categories = models.ManyToManyField(
        "catalog.Category",
        verbose_name="Категорії товарів",
        related_name="picker_doors",
        blank=True,
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показувати", default=True)

    class Meta:
        verbose_name = "Тип дверей (підбір)"
        verbose_name_plural = "Типи дверей (підбір)"
        ordering = ["sort_order", "pk"]

    def __str__(self) -> str:
        return self.display_name("ua")

    def display_name(self, lang: str = "ua") -> str:
        if lang == "ru":
            a = (self.label_line1_ru or self.label_line1).strip()
            b = (self.label_line2_ru or self.label_line2).strip()
        else:
            a = self.label_line1.strip()
            b = self.label_line2.strip()
        return f"{a} {b}".strip() or self.code

    def line1(self, lang: str = "ua") -> str:
        if lang == "ru" and self.label_line1_ru.strip():
            return self.label_line1_ru
        return self.label_line1

    def line2(self, lang: str = "ua") -> str:
        if lang == "ru" and self.label_line2_ru.strip():
            return self.label_line2_ru
        return self.label_line2


class PickerFilter(models.Model):
    KEY_MECH = "mech"
    KEY_BRAND = "brand"
    KEY_PRICE = "price"
    KEY_COLOR = "color"
    KEY_CHOICES = (
        (KEY_MECH, "Тип замка"),
        (KEY_BRAND, "Бренд"),
        (KEY_PRICE, "Ціновий діапазон"),
        (KEY_COLOR, "Колір/покриття"),
    )

    key = models.SlugField("Ключ", max_length=64, unique=True)
    attribute = models.ForeignKey(
        "catalog.Attribute",
        verbose_name="Фільтр каталогу",
        related_name="picker_filters",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    label = models.CharField("Назва", max_length=80)
    label_ru = models.CharField("Назва (RU)", max_length=80, blank=True, default="")
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показувати", default=True)

    class Meta:
        verbose_name = "Фільтр підбору"
        verbose_name_plural = "Фільтри підбору"
        ordering = ["sort_order", "pk"]

    def __str__(self) -> str:
        return self.label or self.key

    def display_label(self, lang: str = "ua") -> str:
        if lang == "ru" and self.label_ru.strip():
            return self.label_ru
        return self.label


class PickerFilterOption(models.Model):
    filter = models.ForeignKey(
        PickerFilter,
        verbose_name="Фільтр",
        related_name="options",
        on_delete=models.CASCADE,
    )
    label = models.CharField("Назва", max_length=80)
    label_ru = models.CharField("Назва (RU)", max_length=80, blank=True, default="")
    value = models.CharField("Значення", max_length=80)
    price_min = models.DecimalField(
        "Ціна від", max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_max = models.DecimalField(
        "Ціна до", max_digits=10, decimal_places=2, null=True, blank=True
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показувати", default=True)

    class Meta:
        verbose_name = "Варіант фільтра"
        verbose_name_plural = "Варіанти фільтрів"
        ordering = ["sort_order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["filter", "value"],
                name="picker_option_unique_value",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.filter_id}: {self.label}"

    def display_label(self, lang: str = "ua") -> str:
        if lang == "ru" and self.label_ru.strip():
            return self.label_ru
        return self.label
