"""Публічний пошук міст і відділень. Помилка бази не віддається як 500."""

from __future__ import annotations

import logging
import uuid

from django.http import JsonResponse
from django.views import View

from novaposhta.present import city_public, warehouse_public
from novaposhta.search import has_data, search_cities, search_warehouses

logger = logging.getLogger(__name__)


def _lang(request) -> str:
    return (getattr(request, 'LANGUAGE_CODE', None) or 'ua')[:2]


def _query(request) -> str:
    return (request.GET.get('q') or '').strip()[:100]


def _city_ref(request) -> str:
    raw = (request.GET.get('city') or '').strip()
    if not raw or len(raw) > 36:
        return ''
    try:
        uuid.UUID(raw)
    except ValueError:
        return ''
    return raw


def _response(payload, status=200):
    response = JsonResponse(payload, status=status, json_dumps_params={'ensure_ascii': False})
    response['X-Robots-Tag'] = 'noindex, nofollow'
    response['Cache-Control'] = 'private, max-age=60'
    return response


def _empty():
    return _response({'available': False, 'items': []})


class CitiesApiView(View):
    def get(self, request):
        try:
            if not has_data():
                return _empty()
            lang = _lang(request)
            items = [city_public(city, lang) for city in search_cities(_query(request))]
            return _response({'available': True, 'items': items})
        except Exception:
            logger.exception('np cities api failed')
            return _empty()


class WarehousesApiView(View):
    def get(self, request):
        try:
            if not has_data():
                return _empty()
            lang = _lang(request)
            city_ref = _city_ref(request)
            items = [
                warehouse_public(row, lang)
                for row in search_warehouses(_query(request), city_ref=city_ref or None)
            ]
            return _response({'available': True, 'items': items})
        except Exception:
            logger.exception('np warehouses api failed')
            return _empty()
