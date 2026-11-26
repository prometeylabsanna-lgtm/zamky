"""Автоконвертація ImageField → WebP при новому аплоаді з адмінки."""

from __future__ import annotations

from django.db import models
from django.db.models.signals import post_save, pre_save

from pages.image_webp import (
    apply_webp_to_image_field,
    ensure_card_sidecar,
    flush_pending_webp_deletes,
    iter_image_fields,
)


def convert_image_field_to_webp(instance, field_name: str, *, quality: int = 88) -> None:
    del quality
    apply_webp_to_image_field(instance, field_name, force=False)


def convert_instance_images_to_webp(sender, instance, **kwargs):
    if not isinstance(instance, models.Model):
        return
    if instance.__class__.__name__ == 'MediaItem':
        return
    for field_name in iter_image_fields(type(instance)):
        apply_webp_to_image_field(instance, field_name, force=False)
        ensure_card_sidecar(getattr(instance, field_name, None))


def delete_replaced_webp_sources(sender, instance, **kwargs):
    if not isinstance(instance, models.Model):
        return
    flush_pending_webp_deletes(instance)


def connect_webp_signals() -> None:
    pre_save.connect(convert_instance_images_to_webp, dispatch_uid='zamky_webp_images')
    post_save.connect(
        delete_replaced_webp_sources,
        dispatch_uid='zamky_webp_images_cleanup',
    )
