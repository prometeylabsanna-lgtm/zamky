"""Нормалізація запитів довідника Нової пошти."""

from __future__ import annotations

import re

_APOSTROPHES = "ʼ'’‘`´ʹ`"
_CHAR_MAP = str.maketrans(
    {
        'ё': 'е',
        'є': 'е',
        'э': 'е',
        'ї': 'и',
        'і': 'и',
        'ы': 'и',
        'и': 'и',
        'ґ': 'г',
    }
)
# Англійська QWERTY → українська ЙЦУКЕН.
_LATIN_TO_CYR = str.maketrans(
    {
        'q': 'й',
        'w': 'ц',
        'e': 'у',
        'r': 'к',
        't': 'е',
        'y': 'н',
        'u': 'г',
        'i': 'ш',
        'o': 'щ',
        'p': 'з',
        '[': 'х',
        ']': 'ї',
        'a': 'ф',
        's': 'і',
        'd': 'в',
        'f': 'а',
        'g': 'п',
        'h': 'р',
        'j': 'о',
        'k': 'л',
        'l': 'д',
        ';': 'ж',
        "'": 'є',
        'z': 'я',
        'x': 'ч',
        'c': 'с',
        'v': 'м',
        'b': 'и',
        'n': 'т',
        'm': 'ь',
        ',': 'б',
        '.': 'ю',
        '`': "'",
    }
)
_NUMBER_RES = (
    re.compile(r'^(?:№|#)\s*(\d+)$'),
    re.compile(r'^[n]\s*(\d+)$'),
    re.compile(r'^(?:відділення|отделение|поштомат)\s*(?:№|#)?\s*(\d+)$', re.IGNORECASE),
    re.compile(r'^(\d+)$'),
)


def normalize(text) -> str:
    if not text:
        return ''
    value = str(text).casefold()
    for char in _APOSTROPHES:
        value = value.replace(char, '')
    value = value.translate(_CHAR_MAP)
    chars = []
    for char in value:
        if char.isalnum() or char.isspace():
            chars.append(char)
        else:
            chars.append(' ')
    return ' '.join(''.join(chars).split())


def latin_to_cyr(text) -> str:
    if not text:
        return ''
    return str(text).casefold().translate(_LATIN_TO_CYR)


def has_latin(text) -> bool:
    return any('a' <= char <= 'z' for char in str(text or '').casefold())


def parse_number(query) -> str | None:
    if not query:
        return None
    compact = ' '.join(str(query).strip().split())
    for pattern in _NUMBER_RES:
        match = pattern.match(compact)
        if match:
            return match.group(1)
    return None


def city_search_norm(name='', name_ru='', area='', region='') -> str:
    parts = [name or '', name_ru or '', area or '', region or '']
    return normalize(' '.join(part for part in parts if part))


def warehouse_search_norm(
    number='',
    description='',
    description_ru='',
    short_address='',
    short_address_ru='',
    city_name='',
    city_name_ru='',
) -> str:
    parts = [
        number or '',
        description or '',
        description_ru or '',
        short_address or '',
        short_address_ru or '',
        city_name or '',
        city_name_ru or '',
    ]
    return normalize(' '.join(part for part in parts if part))
