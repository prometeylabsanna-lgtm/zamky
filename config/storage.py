"""Storage для Vercel-preview: файли з репо `static/`, URL через CDN."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.files.storage import Storage
from django.templatetags.static import static
from django.utils.deconstruct import deconstructible


@deconstructible
class StaticRefStorage(Storage):
    """Читає/віддає файли з BASE_DIR/static без запису на диск (read-only FS)."""

    def _abs(self, name: str) -> Path:
        return Path(settings.BASE_DIR) / 'static' / name

    def _open(self, name, mode='rb'):
        return self._abs(name).open(mode)

    def _save(self, name, content):
        # На Vercel FS read-only — seed лише присвоює name, без запису.
        return name

    def exists(self, name):
        return self._abs(name).exists()

    def url(self, name):
        return static(name)

    def path(self, name):
        return str(self._abs(name))

    def size(self, name):
        return self._abs(name).stat().st_size

    def delete(self, name):
        return None
