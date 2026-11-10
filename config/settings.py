import os
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# Vercel free preview: без Project Env. Прод на DO — тільки через env.
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
    'django.forms',
    'catalog.apps.CatalogConfig',
    'cart.apps.CartConfig',
    'orders.apps.OrdersConfig',
    'pages.apps.PagesConfig',
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'config.middleware.AdminUkrainianLocaleMiddleware',
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

# На Vercel файлова система read-only; SQLite лише в /tmp (дані злітають після cold start).
_DB_NAME = Path('/tmp/zamky.sqlite3') if IS_VERCEL else (BASE_DIR / 'db.sqlite3')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _DB_NAME,
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# G7: у prod без static content fallback. Dev/Vercel-демо — дозволено.
CMS_ALLOW_STATIC_FALLBACK = config(
    'CMS_ALLOW_STATIC_FALLBACK',
    default=DEBUG or IS_VERCEL,
    cast=bool,
)

SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SESSION_SAVE_EVERY_REQUEST = False

DISTRICTS_JSON = BASE_DIR / 'config' / 'districts.json'

def _content_sidebar_groups():
    from pages.site_content_registry import build_content_sidebar_groups

    return build_content_sidebar_groups()


def _admin_link(suffix: str):
    return f'/admin/{suffix.lstrip("/")}'


UNFOLD = {
    'SITE_TITLE': 'Замки',
    'SITE_HEADER': 'Замки — адмінка',
    'SITE_SYMBOL': 'lock',
    # Plain paths — Vercel JSON-сериалізує settings (без reverse/static callables).
    'SITE_FAVICONS': [
        {
            'rel': 'icon',
            'href': '/static/img/favicon.ico',
            'sizes': 'any',
        },
        {
            'rel': 'icon',
            'type': 'image/png',
            'sizes': '32x32',
            'href': '/static/img/favicon-32x32.png',
        },
        {
            'rel': 'icon',
            'type': 'image/png',
            'sizes': '16x16',
            'href': '/static/img/favicon-16x16.png',
        },
        {
            'rel': 'apple-touch-icon',
            'sizes': '180x180',
            'href': '/static/img/apple-touch-icon.png',
        },
    ],
    # Градієнт іконки: #FF8008 (верх) → #FF4B2B (низ)
    'COLORS': {
        'primary': {
            '50': '255 244 237',
            '100': '255 228 214',
            '200': '255 200 176',
            '300': '255 160 120',
            '400': '255 112 64',
            '500': '255 128 8',
            '600': '255 75 43',
            '700': '220 58 28',
            '800': '180 42 22',
            '900': '140 32 16',
            '950': '80 18 10',
        },
    },
    'STYLES': [
        '/static/css/admin/zamky_unfold.css',
    ],
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': False,
        'navigation': [
            {
                'title': 'Налаштування',
                'items': [
                    {
                        'title': 'Контакти та SEO',
                        'icon': 'settings',
                        'link': _admin_link('pages/sitesettings/'),
                    },
                    {
                        'title': 'Медіатека',
                        'icon': 'photo_library',
                        'link': _admin_link('pages/mediaitem/'),
                    },
                    {
                        'title': 'Недавні дії',
                        'icon': 'history',
                        'link': '/admin/recent-actions/',
                    },
                ],
            },
            *_content_sidebar_groups(),
            {
                'title': 'Каталог',
                'separator': True,
                'collapsible': True,
                'items': [
                    {
                        'title': 'Товари',
                        'icon': 'inventory_2',
                        'link': _admin_link('catalog/product/'),
                    },
                    {
                        'title': 'Категорії',
                        'icon': 'category',
                        'link': _admin_link('catalog/category/'),
                    },
                    {
                        'title': 'Фільтри каталогу',
                        'icon': 'tune',
                        'link': _admin_link('catalog/attribute/'),
                    },
                    {
                        'title': 'Значення фільтрів',
                        'icon': 'label',
                        'link': _admin_link('catalog/attributevalue/'),
                    },
                ],
            },
            {
                'title': 'Замовлення',
                'separator': True,
                'collapsible': True,
                'items': [
                    {
                        'title': 'Замовлення',
                        'icon': 'shopping_cart',
                        'link': _admin_link('orders/order/'),
                    },
                    {
                        'title': 'Швидкі замовлення',
                        'icon': 'bolt',
                        'link': _admin_link('orders/quickorder/'),
                    },
                    {
                        'title': 'Райони доставки',
                        'icon': 'map',
                        'link': _admin_link('orders/deliverydistrict/'),
                    },
                ],
            },
            {
                'title': 'Заявки',
                'separator': True,
                'collapsible': True,
                'items': [
                    {
                        'title': 'Контакти',
                        'icon': 'mail',
                        'link': _admin_link('pages/contactrequest/'),
                    },
                    {
                        'title': 'Передзвоніть',
                        'icon': 'call',
                        'link': _admin_link('pages/callbackrequest/'),
                    },
                    {
                        'title': 'Монтаж',
                        'icon': 'build',
                        'link': _admin_link('pages/installrequest/'),
                    },
                    {
                        'title': 'Підбір за фото',
                        'icon': 'photo_camera',
                        'link': _admin_link('pages/photopickrequest/'),
                    },
                    {
                        'title': 'Блог',
                        'icon': 'article',
                        'link': _admin_link('pages/blogpost/'),
                    },
                ],
            },
        ],
    },
}
