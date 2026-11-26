"""Конвертація вже збережених зображень у WebP (ідемпотентно)."""

from __future__ import annotations

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from pages.image_webp import (
    apply_webp_to_image_field,
    encode_raster_to_webp,
    ensure_card_sidecar,
    flush_pending_webp_deletes,
    iter_image_fields,
    skip_stored_name,
)


def _iter_models(app_label: str, model_name: str):
    if model_name:
        if '.' in model_name:
            try:
                yield apps.get_model(model_name)
            except LookupError as exc:
                raise CommandError(f'Модель не знайдена: {model_name}') from exc
            return
        if app_label:
            try:
                yield apps.get_model(app_label, model_name)
            except LookupError as exc:
                raise CommandError(f'Модель не знайдена: {app_label}.{model_name}') from exc
            return
        matches = [
            m
            for m in apps.get_models()
            if m.__name__.lower() == model_name.lower() and not m._meta.proxy
        ]
        if len(matches) != 1:
            raise CommandError(f'Уточніть --app для моделі {model_name}')
        yield matches[0]
        return
    for model in apps.get_models():
        if model._meta.proxy or not model._meta.managed:
            continue
        if app_label and model._meta.app_label != app_label:
            continue
        yield model


def _field_names(model) -> list[str]:
    names = list(iter_image_fields(model))
    if model.__name__ == 'MediaItem' and 'file' not in names:
        names.append('file')
    return names


def _read_size(field_file) -> int:
    try:
        return int(field_file.size or 0)
    except Exception:
        return 0


class Command(BaseCommand):
    help = (
        'Конвертує існуючі растрові зображення в ImageField/MediaItem у WebP. '
        'Ідемпотентно: оптимальні .webp не перекодовуються.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Лише звіт, без змін')
        parser.add_argument('--limit', type=int, default=0, help='Макс. кількість конвертацій')
        parser.add_argument('--app', default='', help='Обмежити додатком (catalog, pages, …)')
        parser.add_argument('--model', default='', help='Модель: Product або catalog.Product')

    def handle(self, *args, **options):
        dry = bool(options['dry_run'])
        limit = int(options['limit'] or 0)
        lock_fh = None if dry else self._acquire_lock()
        if lock_fh is False:
            self.stdout.write(self.style.WARNING('convert_images_webp: уже виконується, пропуск'))
            return
        errors: list[str] = []
        try:
            self._convert_all(options, dry, limit, errors)
        finally:
            self._release_lock(lock_fh)

    def _convert_all(self, options, dry, limit, errors):
        converted = skipped = failed = saved_bytes = 0
        for model in _iter_models(options['app'], options['model']):
            fields = _field_names(model)
            if not fields:
                continue
            if limit and converted >= limit:
                break
            qs = model.objects.all().order_by('pk')
            for instance in qs.iterator():
                if limit and converted >= limit:
                    break
                if model.__name__ == 'MediaItem' and getattr(instance, 'media_type', '') != 'image':
                    continue
                for field_name in fields:
                    if limit and converted >= limit:
                        break
                    field_file = getattr(instance, field_name, None)
                    if not field_file or not getattr(field_file, 'name', None):
                        continue
                    status, delta = self._process_field(
                        instance, field_name, dry=dry, errors=errors
                    )
                    if status == 'converted':
                        converted += 1
                        saved_bytes += max(0, delta)
                    elif status == 'failed':
                        failed += 1
                    else:
                        skipped += 1

        mode = 'DRY-RUN' if dry else 'DONE'
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode}: converted={converted} skipped={skipped} failed={failed} '
                f'saved≈{saved_bytes} B'
            )
        )
        for line in errors:
            self.stdout.write(self.style.WARNING(line))

    def _process_field(self, instance, field_name: str, *, dry: bool, errors: list[str]):
        label = f'{instance._meta.label}.{field_name}#{instance.pk}'
        field_file = getattr(instance, field_name)
        name = field_file.name or ''
        if skip_stored_name(name):
            if not dry:
                ensure_card_sidecar(field_file)
            return 'skipped', 0
        try:
            if dry:
                return self._dry_preview(instance, field_name, label, errors)
            before = _read_size(field_file)
            status = apply_webp_to_image_field(instance, field_name, force=True)
            if status != 'converted':
                if status == 'failed':
                    errors.append(f'{label}: немає файлу або битий файл {name}')
                else:
                    ensure_card_sidecar(getattr(instance, field_name, None))
                return status, 0
            instance.save(update_fields=[field_name])
            flush_pending_webp_deletes(instance)
            ensure_card_sidecar(getattr(instance, field_name, None))
            after = _read_size(getattr(instance, field_name))
            self._refresh_media_item(instance)
            self.stdout.write(f'  {label}: {name} → {getattr(instance, field_name).name}')
            return 'converted', before - after
        except Exception as exc:
            errors.append(f'{label}: {exc}')
            return 'failed', 0

    def _dry_preview(self, instance, field_name, label, errors):
        field_file = getattr(instance, field_name)
        name = field_file.name or ''
        try:
            if hasattr(field_file, 'open'):
                field_file.open('rb')
            if hasattr(field_file, 'seek'):
                field_file.seek(0)
            raw = field_file.read() or b''
            if hasattr(field_file, 'seek'):
                field_file.seek(0)
        except Exception as exc:
            errors.append(f'{label}: не вдалося прочитати ({exc})')
            return 'failed', 0
        if not raw:
            errors.append(f'{label}: порожній/відсутній файл {name}')
            return 'failed', 0
        encoded = encode_raster_to_webp(raw, source_name=name)
        if encoded is None:
            return 'skipped', 0
        delta = len(raw) - len(encoded[0])
        self.stdout.write(f'  {label}: {name} → .webp (−{max(0, delta)} B)')
        return 'converted', delta

    def _refresh_media_item(self, instance) -> None:
        if instance.__class__.__name__ != 'MediaItem' or not instance.file:
            return
        import hashlib

        try:
            if hasattr(instance.file, 'open'):
                instance.file.open('rb')
            if hasattr(instance.file, 'seek'):
                instance.file.seek(0)
            raw = instance.file.read() or b''
        except Exception:
            return
        instance.content_hash = hashlib.sha256(raw).hexdigest()
        instance.file_size = len(raw)
        try:
            from PIL import Image

            img = Image.open(instance.file)
            instance.width, instance.height = img.size
        except Exception:
            pass
        instance.save(update_fields=['content_hash', 'file_size', 'width', 'height'])

    def _acquire_lock(self):
        import fcntl

        from django.conf import settings

        from pathlib import Path

        media = Path(settings.MEDIA_ROOT)
        try:
            media.mkdir(parents=True, exist_ok=True)
            fh = open(media / '.webp_convert.lock', 'a', encoding='utf-8')
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fh
        except BlockingIOError:
            return False
        except Exception:
            return None

    def _release_lock(self, lock_fh) -> None:
        if not lock_fh:
            return
        import fcntl

        try:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            lock_fh.close()
        except Exception:
            pass
