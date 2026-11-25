"""Товари секції «Популярні» на головній."""

from __future__ import annotations

from django.db import models


class HomePopularProduct(models.Model):
    class Tab(models.TextChoices):
        HITS = "hits", "Хіти продажу"
        NEWS = "news", "Новинки"
        SALES = "sales", "Знижки"

    tab = models.CharField(
        "Вкладка",
        max_length=16,
        choices=Tab.choices,
        default=Tab.HITS,
        db_index=True,
    )
    product = models.ForeignKey(
        "catalog.Product",
        verbose_name="Товар",
        related_name="home_popular_slots",
        on_delete=models.CASCADE,
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показувати", default=True)

    class Meta:
        verbose_name = "Товар у популярних"
        verbose_name_plural = "Товари в популярних"
        ordering = ["tab", "sort_order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["tab", "product"],
                name="uniq_home_popular_tab_product",
            ),
        ]

    def __str__(self) -> str:
        name = getattr(self.product, "name", "") or self.product_id
        return f"{self.get_tab_display()}: {name}"

    def save(self, *args, **kwargs):
        from catalog.filter_sort import apply_auto_sort_order

        apply_auto_sort_order(
            self, HomePopularProduct.objects.filter(tab=self.tab)
        )
        super().save(*args, **kwargs)
