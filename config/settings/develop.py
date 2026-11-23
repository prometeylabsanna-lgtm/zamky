import os
from pathlib import Path

from decouple import Csv, config

from .base import *

# Vercel free preview: без Project Env. Прод на DO — config.settings.docker.
IS_VERCEL = bool(os.environ.get('VERCEL'))

SECRET_KEY = config(
    'SECRET_KEY',
    default='vercel-demo-insecure-key-replace-on-digitalocean',
)
DEBUG = config('DEBUG', default=IS_VERCEL, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,.vercel.app',
    cast=Csv(),
)
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://*.vercel.app',
    cast=Csv(),
)

# На Vercel файлова система read-only; SQLite лише в /tmp (дані злітають після cold start).
_DB_NAME = Path('/tmp/zamky.sqlite3') if IS_VERCEL else (BASE_DIR / 'db.sqlite3')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _DB_NAME,
    }
}

MEDIA_ROOT = Path('/tmp/zamky-media') if IS_VERCEL else (BASE_DIR / 'media')

# На Vercel media з /tmp нестабільні між інстансами — демо-фото з static/ через CDN.
if IS_VERCEL:
    STORAGES = {
        'default': {
            'BACKEND': 'config.storage.StaticRefStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

# G7: у prod без static content fallback. Dev/Vercel-демо — дозволено.
CMS_ALLOW_STATIC_FALLBACK = config(
    'CMS_ALLOW_STATIC_FALLBACK',
    default=DEBUG or IS_VERCEL,
    cast=bool,
)
