"""Пошук міст і відділень по вже нормалізованому search_norm."""

from __future__ import annotations

from django.db.models import Case, IntegerField, Q, Value, When
from django.db.models.functions import Coalesce

from config.cache_safe import cache_delete, cache_get, cache_set
from novaposhta.models import NPCity, NPWarehouse
from novaposhta.normalize import has_latin, latin_to_cyr, normalize, parse_number

_HAS_DATA_KEY = 'novaposhta.has_data'
_HAS_DATA_TTL = 300
_CARGO = 'Cargo'


def has_data() -> bool:
    cached = cache_get(_HAS_DATA_KEY, default=None)
    if cached is True or cached is False:
        return cached
    exists = NPWarehouse.objects.filter(is_active=True).exists()
    cache_set(_HAS_DATA_KEY, bool(exists), timeout=_HAS_DATA_TTL)
    return bool(exists)


def invalidate_has_data() -> None:
    cache_delete(_HAS_DATA_KEY)


def search_cities(query, limit=20):
    return _search_cities(query, limit, allow_layout=True)


def search_warehouses(query, city_ref=None, limit=30):
    return _search_warehouses(query, city_ref, limit, allow_layout=True)


def _search_cities(query, limit, allow_layout):
    normalized = normalize(query)
    if len(normalized) < 2:
        if allow_layout and has_latin(query):
            return _search_cities(latin_to_cyr(query), limit, allow_layout=False)
        return []
    rough = Case(
        When(search_norm__startswith=normalized, then=Value(0)),
        default=Value(1),
        output_field=IntegerField(),
    )
    rows = list(
        NPCity.objects.filter(is_active=True, search_norm__contains=normalized)
        .annotate(rough=rough)
        .order_by('rough', 'name')[:300]
    )
    if not rows and allow_layout and has_latin(query):
        altered = latin_to_cyr(query)
        if normalize(altered) != normalized:
            return _search_cities(altered, limit, allow_layout=False)
    ranked = sorted(rows, key=lambda city: (_city_rank(city, normalized), city.name or ''))
    return ranked[:limit]


def _city_base(name: str) -> str:
    raw = name or ''
    head, sep, _rest = raw.partition(' (')
    return normalize(head if sep else raw)


def _city_rank(city, normalized: str) -> int:
    bases = [item for item in (_city_base(city.name), _city_base(city.name_ru)) if item]
    if any(item == normalized for item in bases):
        return 0
    if any(item.startswith(normalized) for item in bases):
        return 1
    if any(normalized in item for item in bases):
        return 2
    return 3


def _search_warehouses(query, city_ref, limit, allow_layout):
    normalized = normalize(query)
    number = parse_number(query)
    tokens = [token for token in normalized.split() if token]
    if len(normalized) < 2 and not number:
        if allow_layout and has_latin(query):
            return _search_warehouses(latin_to_cyr(query), city_ref, limit, allow_layout=False)
        return []
    rows = list(_warehouse_query(normalized, tokens, number, city_ref, limit))
    if not rows and allow_layout and has_latin(query):
        altered = latin_to_cyr(query)
        if normalize(altered) != normalized or parse_number(altered) != number:
            return _search_warehouses(altered, city_ref, limit, allow_layout=False)
    return rows


def _warehouse_query(normalized, tokens, number, city_ref, limit):
    qs = NPWarehouse.objects.filter(is_active=True, is_selectable=True).exclude(category=_CARGO)
    if city_ref:
        qs = qs.filter(city_ref=city_ref)
    text_q = Q()
    for token in tokens:
        text_q &= Q(search_norm__contains=token)
    number_q = Q()
    if number:
        number_q = Q(number=number) | Q(number__startswith=number)
    if number and tokens:
        qs = qs.filter(number_q | text_q)
    elif number:
        qs = qs.filter(number_q)
    elif tokens:
        qs = qs.filter(text_q)
    else:
        return qs.none()

    rank_whens = []
    if number:
        rank_whens.append(When(number=number, then=Value(0)))
        rank_whens.append(When(number__startswith=number, then=Value(1)))
    if normalized:
        rank_whens.append(When(search_norm__startswith=normalized, then=Value(2)))
    rank = Case(*rank_whens, default=Value(3), output_field=IntegerField())
    category_rank = Case(
        When(category='Branch', then=Value(0)),
        When(category='Postomat', then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
    return (
        qs.annotate(
            rank=rank,
            category_rank=category_rank,
            number_sort=Coalesce('number_int', Value(2147483647), output_field=IntegerField()),
        )
        .order_by('rank', 'category_rank', 'number_sort', 'number')[:limit]
    )
