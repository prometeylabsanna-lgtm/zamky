from decouple import Csv, config

from .base import *

# Локальний SQLite. Прод на DigitalOcean — config.settings.docker.
SECRET_KEY = config(
    'SECRET_KEY',
    default='local-dev-insecure-key-do-not-use-in-production',
)
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,[::1],testserver',
    cast=Csv(),
)
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=Csv(),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

MEDIA_ROOT = BASE_DIR / 'media'

CMS_ALLOW_STATIC_FALLBACK = config(
    'CMS_ALLOW_STATIC_FALLBACK',
    default=DEBUG,
    cast=bool,
)

PAYMENT_STUB_ENABLED = True
PAYMENT_WEBHOOK_SECRET = config(
    'PAYMENT_WEBHOOK_SECRET',
    default='dev-payment-webhook-secret',
)
