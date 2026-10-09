import json

from django.conf import settings

from catalog.menu import menu_payload
from orders.models import DeliveryDistrict
from pages.i18n_lib import js_i18n_dict, site_lang_code, tr

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

    return {
        'site_city': city,
        'site_districts': districts,
        'selected_district': selected,
        'selected_district_slug': selected_slug,
        'site_lang': site_lang_code(),
        'header_menu': menu_payload(),
        'header_catalog_active': url_name in CATALOG_URL_NAMES,
        'js_i18n': js_i18n_dict(),
        # bump when CSS/JS change so browsers drop stale DevTools cache
        'asset_v': '20261008t',
    }
