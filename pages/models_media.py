"""Спільна медіатека (MediaItem)."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models

from pages.image_webp import encode_raster_to_webp, is_uncommitted_upload, queue_old_file_delete


class MediaItem(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Зображення"
        VIDEO = "video", "Відео"
        DOC = "doc", "Документ"

    file = models.FileField("Файл", upload_to="media_library/%Y/%m/")
    media_type = models.CharField(
        "Тип",
        max_length=8,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
    )
    title = models.CharField("Назва", max_length=255, blank=True, default="")
    alt_text = models.CharField("Alt", max_length=255, blank=True, default="")
    alt_text_ru = models.CharField("Alt (RU)", max_length=255, blank=True, default="")
    width = models.PositiveIntegerField("Ширина", null=True, blank=True, editable=False)
    height = models.PositiveIntegerField("Висота", null=True, blank=True, editable=False)
    file_size = models.PositiveIntegerField("Розмір файлу", default=0, editable=False)
    content_hash = models.CharField(
        "SHA-256", max_length=64, blank=True, default="", db_index=True, editable=False
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        editable=False,
        related_name="uploaded_media",
    )
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Медіафайл"
        verbose_name_plural = "Медіатека"

    def __str__(self):
        if self.title:
            return self.title
        if self.file:
            return Path(self.file.name).name
        return f"Media #{self.pk}"

    @property
    def url(self) -> str:
        try:
            return self.file.url
        except Exception:
            return ""

    def save(self, *args, **kwargs):
        converting = bool(
            self.file
            and self.media_type == self.MediaType.IMAGE
            and (not self.content_hash or is_uncommitted_upload(self.file))
        )
        if converting:
            self._prepare_image_webp()
        elif self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    def _read_bytes(self) -> bytes:
        f = self.file
        try:
            if hasattr(f, "open"):
                f.open("rb")
            if hasattr(f, "seek"):
                f.seek(0)
            data = f.read()
            if hasattr(f, "seek"):
                f.seek(0)
            return data or b""
        except Exception:
            return b""

    def _prepare_image_webp(self) -> None:
        raw = self._read_bytes()
        if not raw:
            return

        name = getattr(self.file, "name", "image") or "image"
        encoded = encode_raster_to_webp(raw, source_name=name)
        stored = encoded[0] if encoded else raw
        digest = hashlib.sha256(stored).hexdigest()
        existing = (
            MediaItem.objects.filter(content_hash=digest).exclude(pk=self.pk).first()
        )
        if existing and existing.file:
            self.file = existing.file
            self.width = existing.width
            self.height = existing.height
            self.file_size = existing.file_size
            self.content_hash = digest
            return

        width = height = None
        if encoded:
            width, height = encoded[1], encoded[2]
        else:
            try:
                from PIL import Image

                img = Image.open(io.BytesIO(raw))
                width, height = img.size
            except Exception:
                pass

        prev = self.file.name if self.pk else ""
        self.content_hash = digest
        self.file_size = len(stored)
        self.width = width
        self.height = height
        if encoded:
            stem = Path(name).stem or "image"
            self.file.save(f"{stem}.webp", ContentFile(stored), save=False)
            new_name = self.file.name or ""
            if prev and prev != new_name:
                queue_old_file_delete(self, prev)
