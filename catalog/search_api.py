"""JSON API підказок пошуку."""

from django.http import JsonResponse
from django.urls import reverse
from django.utils.http import urlencode
from django.views import View

from catalog.search import suggest


class SearchSuggestApiView(View):
    def get(self, request):
        q = (request.GET.get('q') or '').strip()
        items = suggest(q, limit=8)
        catalog_url = reverse('catalog:catalog')
        for item in items:
            if item.get('type') == 'brand':
                item['url'] = f'{catalog_url}?{urlencode({"q": item["label"]})}'
        return JsonResponse(
            {
                'query': q,
                'items': items,
                'all_url': f'{catalog_url}?{urlencode({"q": q})}' if q else catalog_url,
            }
        )
