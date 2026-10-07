import json

from django.conf import settings

from orders.models import DeliveryDistrict


def site_context(request):
    districts = list(
        DeliveryDistrict.objects.filter(is_active=True).values(
            'slug', 'name', 'short', 'name_locative', 'delivery_note'
        )
    )
    city = {'slug': 'kyiv', 'name': 'Київ', 'name_genitive': 'Києва'}
    path = settings.DISTRICTS_JSON
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            city = data.get('city', city)
        except (OSError, json.JSONDecodeError):
            pass

    selected_slug = request.session.get('district_slug')
    selected = None
    if selected_slug:
        selected = next((d for d in districts if d['slug'] == selected_slug), None)

    return {
        'site_city': city,
        'site_districts': districts,
        'selected_district': selected,
        'selected_district_slug': selected_slug,
    }
