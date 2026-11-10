import json
import uuid

from django.conf import settings

from catalog.menu import menu_payload
from orders.models import DeliveryDistrict
from pages.cms_content import get_block_text, get_site_blocks_map
from pages.i18n_lib import js_i18n_dict, site_lang_code, tr
from pages.models_cms import SiteSettings
from pages.page_styles import get_page_style_vars

CATALOG_URL_NAMES = {'product', 'catalog', 'category'}


def site_context(request):
    districts = list(
        DeliveryDistrict.objects.filter(is_active=True).values(
            'slug', 'name', 'short', 'name_locative', 'delivery_note'
        )
    )
    for row in districts:
        row['name'] = tr(row['name'])
        row['short'] = tr(row['short'])
        row['name_locative'] = tr(row['name_locative'])
        row['delivery_note'] = tr(row['delivery_note'])

    city = {'slug': 'kyiv', 'name': tr('Київ'), 'name_genitive': tr('Києва')}
    path = settings.DISTRICTS_JSON
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            raw_city = data.get('city', {})
            city = {
                'slug': raw_city.get('slug', 'kyiv'),
                'name': tr(raw_city.get('name', 'Київ')),
                'name_genitive': tr(raw_city.get('name_genitive', 'Києва')),
            }
        except (OSError, json.JSONDecodeError):
            pass

    selected_slug = request.session.get('district_slug')
    selected = None
    if selected_slug:
        selected = next((d for d in districts if d['slug'] == selected_slug), None)

    url_name = ''
    if request.resolver_match:
        url_name = request.resolver_match.url_name or ''

    cb_key = request.session.get('callback_idempotency') or uuid.uuid4().hex
    request.session['callback_idempotency'] = cb_key

    lang = (getattr(request, 'LANGUAGE_CODE', None) or 'ua')[:2].lower()
    if lang == 'uk':
        lang = 'ua'
    site_blocks = get_site_blocks_map()
    try:
        site_settings = SiteSettings.load()
    except Exception:
        site_settings = None

    def cms(page, key, fallback=''):
        return get_block_text(
            page, key, lang=lang, site_blocks=site_blocks, fallback=fallback
        )

    return {
        'site_city': city,
        'site_districts': districts,
        'selected_district': selected,
        'selected_district_slug': selected_slug,
        'site_lang': site_lang_code(),
        'cms_lang': lang,
        'site_blocks': site_blocks,
        'site_settings': site_settings,
        'cms_header_catalog': cms('site', 'header_catalog_label', 'Каталог'),
        'cms_header_search': cms(
            'site', 'header_search_placeholder', 'Пошук замків, циліндрів…'
        ),
        'cms_header_callback': cms('site', 'header_callback_label', 'Передзвоніть мені'),
        'cms_footer_about_title': cms('site', 'footer_about_title'),
        'cms_footer_about_text': cms('site', 'footer_about_text'),
        'cms_footer_catalog_title': cms('site', 'footer_catalog_title', 'Каталог'),
        'cms_footer_info_title': cms('site', 'footer_info_title', 'Інформація'),
        'cms_footer_contacts_title': cms('site', 'footer_contacts_title', 'Контакти'),
        'cms_footer_copyright': cms('site', 'footer_copyright'),
        'header_menu': menu_payload(),
        'header_catalog_active': url_name in CATALOG_URL_NAMES,
        'js_i18n': js_i18n_dict(),
        'callback_idempotency': cb_key,
        'page_style': _safe_page_style(request),
        # bump when CSS/JS change so browsers drop stale DevTools cache
        'asset_v': '20261110v13',
    }


def _safe_page_style(request):
    try:
        return get_page_style_vars(request)
    except Exception:
        return {"bg": "", "text": "", "accent": ""}
