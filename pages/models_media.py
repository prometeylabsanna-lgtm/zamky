"""Спільна медіатека (MediaItem)."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models


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
            and not self.content_hash
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
        try:
            from PIL import Image
        except ImportError:
            return

        raw = self._read_bytes()
        if not raw:
            return

        digest = hashlib.sha256(raw).hexdigest()
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

        try:
            img = Image.open(io.BytesIO(raw))
            img.load()
        except Exception:
            self.content_hash = digest
            self.file_size = len(raw)
            return

        self.width, self.height = img.size
        has_alpha = img.mode in {"RGBA", "LA"} or (
            img.mode == "P" and "transparency" in img.info
        )
        img = img.convert("RGBA" if has_alpha else "RGB")

        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=82, method=4)
        data = buf.getvalue()
        self.content_hash = hashlib.sha256(data).hexdigest()
        self.file_size = len(data)

        stem = Path(getattr(self.file, "name", "image") or "image").stem or "image"
        content = ContentFile(data)
        # FieldFile.save замінює файл без повторного читання closed upload
        self.file.save(f"{stem}.webp", content, save=False)
