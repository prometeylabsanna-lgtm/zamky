import sys

from decouple import Csv, UndefinedValueError, config
from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

try:
    SECRET_KEY = config('SECRET_KEY')
except UndefinedValueError as exc:
    raise ImproperlyConfigured('SECRET_KEY environment variable is required') from exc
if not str(SECRET_KEY).strip():
    raise ImproperlyConfigured('SECRET_KEY environment variable is required')

ALLOWED_HOSTS = [
    host for host in config('ALLOWED_HOSTS', default='', cast=Csv()) if host
]
CSRF_TRUSTED_ORIGINS = [
    origin
    for origin in config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
    if origin
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# nginx terminates TLS; Gunicorn stays HTTP so /healthz/ is not 301.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = False

USE_HTTPS = config('USE_HTTPS', default=False, cast=bool)
SESSION_COOKIE_SECURE = USE_HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'SAMEORIGIN'
if USE_HTTPS:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
    }
}

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

CMS_ALLOW_STATIC_FALLBACK = False

PAYMENT_WEBHOOK_SECRET = config('PAYMENT_WEBHOOK_SECRET', default='')
if not str(PAYMENT_WEBHOOK_SECRET).strip():
    sys.stderr.write(
        'Попередження: PAYMENT_WEBHOOK_SECRET порожній — вебхук оплати відхиляє запити.\n'
    )
PAYMENT_STUB_ENABLED = False
