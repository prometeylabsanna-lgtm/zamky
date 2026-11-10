"""Унікальні slug для моделей."""

from __future__ import annotations

from django.db.models import Model
from django.utils.text import slugify


def ensure_unique_slug(
    model: type[Model],
    base: str,
    *,
    instance_pk=None,
    field: str = 'slug',
    extra_filter: dict | None = None,
    fallback: str = 'item',
) -> str:
    seed = slugify(base) or fallback
    slug = seed
    i = 1
    qs = model.objects.all()
    if extra_filter:
        qs = qs.filter(**extra_filter)
    while qs.filter(**{field: slug}).exclude(pk=instance_pk).exists():
        slug = f'{seed}-{i}'
        i += 1
    return slug
