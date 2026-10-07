from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'catalog',
    'cart',
    'orders',
    'pages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart_context',
                'pages.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ua'
LANGUAGES = [
    ('ua', 'Українська'),
    ('ru', 'Русский'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGE_COOKIE_NAME = 'zamky_lang'
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LANGUAGE_COOKIE_SAMESITE = 'Lax'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True

# Django не знає код «ua» (є лише «uk»). Реєструємо + гарантуємо .mo,
# інакше runserver падає: OSError: No translation files found for default language ua.
from django.conf.locale import LANG_INFO  # noqa: E402

LANG_INFO['ua'] = {
    'bidi': False,
    'code': 'ua',
    'name': 'Ukrainian',
    'name_local': 'Українська',
}


def _ensure_locale_mo():
    import shutil

    try:
        import django
    except ImportError:
        return
    django_locale = Path(django.__file__).resolve().parent / 'conf' / 'locale'
    for our_code, django_code in (('ua', 'uk'), ('ru', 'ru')):
        dest_dir = BASE_DIR / 'locale' / our_code / 'LC_MESSAGES'
        dest_mo = dest_dir / 'django.mo'
        if dest_mo.exists() and dest_mo.stat().st_size > 0:
            continue
        src = django_locale / django_code / 'LC_MESSAGES' / 'django.mo'
        if not src.exists():
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest_mo)


_ensure_locale_mo()

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SESSION_SAVE_EVERY_REQUEST = False

DISTRICTS_JSON = BASE_DIR / 'config' / 'districts.json'

UNFOLD = {
    'SITE_TITLE': 'Замки',
    'SITE_HEADER': 'Замки — адмінка',
    'SITE_SYMBOL': 'lock',
    'COLORS': {
        'primary': {
            '50': '255 250 235',
            '100': '255 243 204',
            '200': '255 231 163',
            '300': '255 214 102',
            '400': '255 196 0',
            '500': '240 184 0',
            '600': '217 163 0',
            '700': '179 134 0',
            '800': '140 105 0',
            '900': '102 76 0',
            '950': '64 48 0',
        },
    },
}
