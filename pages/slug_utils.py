"""Унікальні slug: українська/російська назва → латиниця."""

from __future__ import annotations

from django.db.models import Model
from django.utils.text import slugify

_CYR = {
    'а': 'a',
    'б': 'b',
    'в': 'v',
    'г': 'h',
    'ґ': 'g',
    'д': 'd',
    'е': 'e',
    'є': 'ie',
    'ж': 'zh',
    'з': 'z',
    'и': 'y',
    'і': 'i',
    'ї': 'i',
    'й': 'i',
    'к': 'k',
    'л': 'l',
    'м': 'm',
    'н': 'n',
    'о': 'o',
    'п': 'p',
    'р': 'r',
    'с': 's',
    'т': 't',
    'у': 'u',
    'ф': 'f',
    'х': 'kh',
    'ц': 'ts',
    'ч': 'ch',
    'ш': 'sh',
    'щ': 'shch',
    'ь': '',
    'ю': 'iu',
    'я': 'ia',
    'ё': 'yo',
    'ы': 'y',
    'э': 'e',
    'ъ': '',
}
_START = {'є': 'ye', 'ї': 'yi', 'й': 'y', 'ю': 'yu', 'я': 'ya'}


def transliterate(text: str) -> str:
    out = []
    start = True
    for char in text or '':
        low = char.lower()
        if low in _CYR or low in _START:
            mapped = _START[low] if start and low in _START else _CYR.get(low, '')
            out.append(mapped)
            start = False
            continue
        if char.isalnum():
            out.append(char)
            start = False
            continue
        out.append('-')
        start = True
    return ''.join(out)


def slug_seed(base: str, fallback: str = 'item') -> str:
    return slugify(transliterate(base)) or slugify(base) or fallback


def should_rebuild_slug(base: str, current: str, fallback: str = 'item') -> bool:
    if not (current or '').strip():
        return True
    seed = slug_seed(base, fallback)
    stripped = slugify(base or '')
    return bool(stripped) and current == stripped and seed != stripped


def ensure_unique_slug(
    model: type[Model],
    base: str,
    *,
    instance_pk=None,
    field: str = 'slug',
    extra_filter: dict | None = None,
    fallback: str = 'item',
) -> str:
    seed = slug_seed(base, fallback)
    slug = seed
    i = 1
    qs = model.objects.all()
    if extra_filter:
        qs = qs.filter(**extra_filter)
    while qs.filter(**{field: slug}).exclude(pk=instance_pk).exists():
        slug = f'{seed}-{i}'
        i += 1
    return slug
