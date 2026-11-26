from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

_admin_path = config('ADMIN_URL', default='admin').strip().strip('/')
if not _admin_path:
    _admin_path = 'admin'
ADMIN_URL = f'{_admin_path}/'

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
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'django.forms',
    'catalog.apps.CatalogConfig',
    'cart.apps.CartConfig',
    'orders.apps.OrdersConfig',
    'novaposhta.apps.NovaposhtaConfig',
    'pages.apps.PagesConfig',
    'marketing.apps.MarketingConfig',
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'config.middleware.RateLimitMiddleware',
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
TEST_RUNNER = 'config.test_runner.TempMediaDiscoverRunner'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SESSION_SAVE_EVERY_REQUEST = False

PAYMENT_WEBHOOK_SECRET = config('PAYMENT_WEBHOOK_SECRET', default='')
PAYMENT_STUB_ENABLED = False
PAYMENT_RESERVE_MINUTES = 30
PAYMENT_ONLINE_ENABLED = config('PAYMENT_ONLINE_ENABLED', default=False, cast=bool)
LIQPAY_PUBLIC_KEY = config('LIQPAY_PUBLIC_KEY', default='')
LIQPAY_PRIVATE_KEY = config('LIQPAY_PRIVATE_KEY', default='')

# Довідник відділень працює і з порожнім ключем. Ключ бізнес-кабінету — для ТТН.
NOVA_POSHTA_API_KEY = config('NOVA_POSHTA_API_KEY', default='')
NOVA_POSHTA_API_URL = config(
    'NOVA_POSHTA_API_URL',
    default='https://api.novaposhta.ua/v2.0/json/',
)

DISTRICTS_JSON = BASE_DIR / 'config' / 'districts.json'


def _content_sidebar_groups():
    from pages.site_content_registry import build_content_sidebar_groups

    return build_content_sidebar_groups(admin_prefix=ADMIN_URL)


def _admin_link(suffix: str):
    return f'/{ADMIN_URL.strip("/")}/{suffix.lstrip("/")}'


def _admin_nav_active(suffix: str):
    """Лише цей розділ: /attribute/ не чіпає /attributegroup/."""
    base = _admin_link(suffix).rstrip('/')

    def _is_active(request):
        path = (getattr(request, 'path', None) or '').rstrip('/')
        if path == base:
            return True
        if not path.startswith(base):
            return False
        return path[len(base) :].startswith('/')

    return _is_active


def _admin_nav_active_any(*suffixes):
    checks = [_admin_nav_active(suffix) for suffix in suffixes]

    def _is_active(request):
        return any(fn(request) for fn in checks)

    return _is_active


UNFOLD = {
    'SITE_TITLE': 'Замки',
    'SITE_HEADER': 'Замки — адмінка',
    'SITE_SYMBOL': 'lock',
    # Plain paths — без reverse/static callables у settings.
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
                        'title': 'Контакти та бренд',
                        'icon': 'settings',
                        'link': _admin_link('pages/sitesettings/'),
                    },
                    {
                        'title': 'Недавні дії',
                        'icon': 'history',
                        'link': _admin_link('recent-actions/'),
                    },
                ],
            },
            {
                'title': 'Маркетинг',
                'separator': True,
                'collapsible': True,
                'items': [
                    {
                        'title': 'Товарні фіди',
                        'icon': 'rss_feed',
                        'link': _admin_link('marketing/productfeed/'),
                    },
                    {
                        'title': 'SEO-налаштування',
                        'icon': 'travel_explore',
                        'link': _admin_link('marketing/seosettings/'),
                    },
                    {
                        'title': 'Пікселі та лічильники',
                        'icon': 'monitoring',
                        'link': _admin_link('marketing/trackingsettings/'),
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
                        'title': 'Характеристики',
                        'icon': 'tune',
                        'link': _admin_link('catalog/attribute/'),
                        'active': _admin_nav_active_any(
                            'catalog/attribute/',
                            'catalog/attributegroup/',
                            'catalog/attributevalue/',
                        ),
                    },
                    {
                        'title': 'Відгуки',
                        'icon': 'reviews',
                        'link': _admin_link('catalog/review/'),
                    },
                    {
                        'title': 'Сімʼї',
                        'icon': 'account_tree',
                        'link': _admin_link('catalog/productfamily/'),
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
                'title': 'Нова Пошта',
                'separator': True,
                'collapsible': True,
                'items': [
                    {
                        'title': 'Відділення НП',
                        'icon': 'local_shipping',
                        'link': _admin_link('novaposhta/npwarehouse/'),
                    },
                    {
                        'title': 'Міста НП',
                        'icon': 'location_city',
                        'link': _admin_link('novaposhta/npcity/'),
                    },
                    {
                        'title': 'Синхронізації НП',
                        'icon': 'sync',
                        'link': _admin_link('novaposhta/npsyncrun/'),
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
                ],
            },
        ],
    },
}
