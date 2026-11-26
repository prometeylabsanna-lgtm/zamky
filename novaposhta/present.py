"""Публічні поля відділення і міста для API та снапшота замовлення."""

from __future__ import annotations


def _pick(lang: str, primary: str, secondary: str) -> str:
    if lang == 'ru' and (secondary or '').strip():
        return secondary.strip()
    return (primary or '').strip()


def warehouse_public(warehouse, lang: str) -> dict:
    label = _pick(lang, warehouse.description, warehouse.description_ru)
    address = _pick(lang, warehouse.short_address, warehouse.short_address_ru)
    city = _pick(lang, warehouse.city_name, warehouse.city_name_ru)
    if not label:
        label = address
    if not label and warehouse.number:
        label = f'№{warehouse.number}'
    return {
        'ref': warehouse.ref,
        'label': label,
        'number': warehouse.number or '',
        'category': warehouse.category or '',
        'address': address,
        'city_ref': warehouse.city_ref or '',
        'city': city,
    }


def city_public(city, lang: str) -> dict:
    label = _pick(lang, city.name, city.name_ru)
    return {
        'ref': city.ref,
        'label': label,
        'number': '',
        'category': '',
        'address': (city.area or '').strip(),
        'city_ref': city.ref,
        'city': label,
    }
