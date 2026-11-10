"""Автоконвертація ImageField → WebP при новому аплоаді з адмінки."""

from __future__ import annotations

import io
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import pre_save


def _is_uncommitted_upload(field_file) -> bool:
    if not field_file or not getattr(field_file, 'name', None):
        return False
    if getattr(field_file, '_committed', True) is False:
        return True
    return False


def convert_image_field_to_webp(instance, field_name: str, *, quality: int = 82) -> None:
    field_file = getattr(instance, field_name, None)
    if not _is_uncommitted_upload(field_file):
        return

    name = (field_file.name or '').lower()
    # Уже webp з аплоаду — лишаємо як є (лише нормалізуємо імʼя за потреби)
    try:
        from PIL import Image
    except ImportError:
        return

    try:
        if hasattr(field_file, 'open'):
            field_file.open('rb')
        if hasattr(field_file, 'seek'):
            field_file.seek(0)
        raw = field_file.read()
        if hasattr(field_file, 'seek'):
            field_file.seek(0)
    except Exception:
        return
    if not raw:
        return

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception:
        return

    has_alpha = img.mode in {'RGBA', 'LA'} or (
        img.mode == 'P' and 'transparency' in img.info
    )
    img = img.convert('RGBA' if has_alpha else 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='WEBP', quality=quality, method=4)
    data = buf.getvalue()

    stem = Path(field_file.name or 'image').stem or 'image'
    # ContentFile + FieldFile.save(save=False) — без повторного model.save
    getattr(instance, field_name).save(
        f'{stem}.webp',
        ContentFile(data),
        save=False,
    )


def convert_instance_images_to_webp(sender, instance, **kwargs):
    if not isinstance(instance, models.Model):
        return
    # MediaItem має власний пайплайн (хеш/дедуп) — не дублюємо
    if instance.__class__.__name__ == 'MediaItem':
        return
    for field in instance._meta.get_fields():
        if not isinstance(field, models.ImageField):
            continue
        convert_image_field_to_webp(instance, field.name)


def connect_webp_signals() -> None:
    pre_save.connect(convert_instance_images_to_webp, dispatch_uid='zamky_webp_images')
