from django import template

from orders.utils import format_uah, plural_goods, plural_positions

register = template.Library()


@register.filter(name='uah')
def uah_filter(value):
    return format_uah(value)


@register.filter(name='plural_positions')
def plural_positions_filter(n):
    return plural_positions(n)


@register.filter(name='plural_goods')
def plural_goods_filter(n):
    return plural_goods(n)


@register.simple_tag
def count_label(n, kind='goods'):
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    word = plural_positions(n) if kind == 'positions' else plural_goods(n)
    return f'{n} {word}'
