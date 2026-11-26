"""Спільна конвертація растру в WebP: якість, EXIF, прозорість, ліміт сторони."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import models

logger = logging.getLogger(__name__)

WEBP_QUALITY = 88
WEBP_METHOD = 6
MAX_SIDE = 2560
CARD_SIDE = 480
CARD_QUALITY = 80
SKIP_EXT = frozenset({'.svg', '.ico', '.gif', '.mp4', '.webm', '.mov', '.pdf'})

_heif_ready = False


def register_heif_opener() -> None:
    global _heif_ready
    if _heif_ready:
        return
    try:
        from pillow_heif import register_heif_opener as _reg

        _reg()
        _heif_ready = True
    except Exception:
        _heif_ready = False


def is_uncommitted_upload(field_file) -> bool:
    if not field_file or not getattr(field_file, 'name', None):
        return False
    return getattr(field_file, '_committed', True) is False


def skip_stored_name(name: str) -> bool:
    """Уже .webp / не растр — не читати з диска (деплой, команда)."""
    ext = Path(name or '').suffix.lower()
    return ext in SKIP_EXT or ext == '.webp'


def _read_field_bytes(field_file) -> bytes:
    try:
        if hasattr(field_file, 'open'):
            field_file.open('rb')
        if hasattr(field_file, 'seek'):
            field_file.seek(0)
        raw = field_file.read()
        if hasattr(field_file, 'seek'):
            field_file.seek(0)
        return raw or b''
    except Exception:
        return b''


def encode_raster_to_webp(raw: bytes, *, source_name: str = '') -> tuple[bytes, int, int] | None:
    """Повертає (webp_bytes, w, h) або None, якщо файл треба лишити як є / не растр."""
    register_heif_opener()
    ext = Path(source_name or '').suffix.lower()
    if ext in SKIP_EXT:
        return None
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError:
        return None
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        return None
    if getattr(img, 'n_frames', 1) > 1:
        return None
    fmt = (img.format or '').upper()
    try:
        img = ImageOps.exif_transpose(img) or img
    except Exception:
        pass
    w, h = img.size
    if not w or not h:
        return None
    already_ok = fmt == 'WEBP' and max(w, h) <= MAX_SIDE
    if already_ok:
        return None
    if max(w, h) > MAX_SIDE:
        ratio = MAX_SIDE / float(max(w, h))
        img = img.resize(
            (max(1, int(w * ratio)), max(1, int(h * ratio))),
            Image.Resampling.LANCZOS,
        )
        w, h = img.size
    has_alpha = img.mode in {'RGBA', 'LA'} or (
        img.mode == 'P' and 'transparency' in img.info
    )
    img = img.convert('RGBA' if has_alpha else 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='WEBP', quality=WEBP_QUALITY, method=WEBP_METHOD)
    data = buf.getvalue()
    if not data:
        return None
    if fmt == 'WEBP' and len(data) >= len(raw):
        return None
    return data, w, h


def _previous_name(instance, field_name: str) -> str:
    if not getattr(instance, 'pk', None):
        return ''
    try:
        return (
            type(instance)
            .objects.filter(pk=instance.pk)
            .values_list(field_name, flat=True)
            .first()
            or ''
        )
    except Exception:
        return ''


def apply_webp_to_image_field(instance, field_name: str, *, force: bool = False) -> str:
    """converted | skipped | failed. force=True — і вже збережені файли (команда)."""
    field_file = getattr(instance, field_name, None)
    if not field_file or not getattr(field_file, 'name', None):
        return 'skipped'
    if not force and not is_uncommitted_upload(field_file):
        return 'skipped'
    name = field_file.name or ''
    if force and skip_stored_name(name):
        return 'skipped'
    if not force:
        ext = Path(name).suffix.lower()
        if ext in SKIP_EXT:
            return 'skipped'
    if force:
        try:
            if not field_file.storage.exists(name):
                return 'failed'
        except Exception:
            return 'failed'
    raw = _read_field_bytes(field_file)
    if not raw:
        return 'failed'
    encoded = encode_raster_to_webp(raw, source_name=name)
    if encoded is None:
        return 'skipped'
    data, _w, _h = encoded
    prev = _previous_name(instance, field_name)
    stem = Path(name).stem or 'image'
    try:
        getattr(instance, field_name).save(
            f'{stem}.webp',
            ContentFile(data),
            save=False,
        )
    except Exception:
        logger.exception('webp save failed %s.%s', type(instance).__name__, field_name)
        return 'failed'
    new_name = getattr(instance, field_name).name or ''
    if prev and prev != new_name:
        queue_old_file_delete(instance, prev)
        sidecar_old = card_sidecar_name(prev)
        if sidecar_old != card_sidecar_name(new_name):
            queue_old_file_delete(instance, sidecar_old)
    return 'converted'


def queue_old_file_delete(instance, name: str) -> None:
    if not name:
        return
    pending = getattr(instance, '_webp_pending_delete', None)
    if pending is None:
        pending = []
        instance._webp_pending_delete = pending
    if name not in pending:
        pending.append(name)


def flush_pending_webp_deletes(instance) -> None:
    pending = getattr(instance, '_webp_pending_delete', None) or []
    if not pending:
        return
    storage = None
    names = list(iter_image_fields(type(instance)))
    if 'file' not in names:
        names.append('file')
    for field_name in names:
        field_file = getattr(instance, field_name, None)
        if field_file is not None and hasattr(field_file, 'storage'):
            storage = field_file.storage
            break
    if storage is None:
        from django.core.files.storage import default_storage

        storage = default_storage
    for name in pending:
        try:
            storage.delete(name)
        except Exception:
            logger.warning('old media not deleted: %s', name)
    instance._webp_pending_delete = []


def iter_image_fields(model):
    for field in model._meta.get_fields():
        if isinstance(field, models.ImageField):
            yield field.name


def card_sidecar_name(name: str) -> str:
    path = Path(name or '')
    if not path.name:
        return ''
    return str(path.with_name(f'{path.stem}-card.webp'))


def encode_resized_webp(
    raw: bytes,
    *,
    max_side: int = CARD_SIDE,
    max_width: int | None = None,
    quality: int = CARD_QUALITY,
    source_name: str = '',
) -> tuple[bytes, int, int] | None:
    register_heif_opener()
    ext = Path(source_name or '').suffix.lower()
    if ext in SKIP_EXT:
        return None
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError:
        return None
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        return None
    if getattr(img, 'n_frames', 1) > 1:
        return None
    try:
        img = ImageOps.exif_transpose(img) or img
    except Exception:
        pass
    w, h = img.size
    if not w or not h:
        return None
    if max_width and w > max_width:
        ratio = max_width / float(w)
        img = img.resize(
            (max_width, max(1, int(h * ratio))),
            Image.Resampling.LANCZOS,
        )
        w, h = img.size
    elif max(w, h) > max_side:
        ratio = max_side / float(max(w, h))
        img = img.resize(
            (max(1, int(w * ratio)), max(1, int(h * ratio))),
            Image.Resampling.LANCZOS,
        )
        w, h = img.size
    has_alpha = img.mode in {'RGBA', 'LA'} or (
        img.mode == 'P' and 'transparency' in img.info
    )
    img = img.convert('RGBA' if has_alpha else 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='WEBP', quality=quality, method=WEBP_METHOD)
    data = buf.getvalue()
    if not data:
        return None
    return data, w, h


def ensure_card_sidecar(field_file, *, max_side: int = CARD_SIDE) -> str:
    """Пише {stem}-card.webp поруч з оригіналом, поле моделі не чіпає."""
    if not field_file or not getattr(field_file, 'name', None):
        return 'skipped'
    name = field_file.name or ''
    if Path(name).stem.endswith('-card'):
        return 'skipped'
    sidecar = card_sidecar_name(name)
    if not sidecar:
        return 'skipped'
    storage = getattr(field_file, 'storage', None)
    if storage is None:
        return 'skipped'
    try:
        if storage.exists(sidecar):
            return 'skipped'
    except Exception:
        return 'failed'
    raw = _read_field_bytes(field_file)
    if not raw:
        return 'failed'
    encoded = encode_resized_webp(
        raw, max_side=max_side, source_name=name
    )
    if encoded is None:
        return 'skipped'
    data, _w, _h = encoded
    try:
        storage.save(sidecar, ContentFile(data))
    except Exception:
        logger.exception('card sidecar save failed %s', sidecar)
        return 'failed'
    return 'converted'


def card_image_url(field_file, *, max_side: int = CARD_SIDE) -> str:
    if not field_file or not getattr(field_file, 'name', None):
        return ''
    sidecar = card_sidecar_name(field_file.name)
    storage = getattr(field_file, 'storage', None)
    if sidecar and storage is not None:
        try:
            if storage.exists(sidecar):
                return storage.url(sidecar)
        except Exception:
            pass
    try:
        return field_file.url or ''
    except Exception:
        return ''
