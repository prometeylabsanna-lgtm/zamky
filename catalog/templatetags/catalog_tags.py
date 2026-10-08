"""Querystring helpers: зберігають multi-value GET (brand=a&brand=b)."""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def keep_query(context, *exclude, **set_params):
    """Зібрати query string з request.GET, виключивши ключі та/або перезаписавши."""
    request = context.get('request')
    if request is None:
        return ''
    qd = request.GET.copy()
    for key in exclude:
        if key:
            qd.pop(key, None)
    for key, value in set_params.items():
        if value is None or value == '':
            qd.pop(key, None)
        else:
            qd[key] = str(value)
    return qd.urlencode()


@register.simple_tag(takes_context=True)
def chip_remove_query(context, key, slug=''):
    """Прибрати один чіп (одне значення з getlist або price_min/max)."""
    request = context.get('request')
    if request is None:
        return ''
    qd = request.GET.copy()
    if key == 'price':
        qd.pop('price_min', None)
        qd.pop('price_max', None)
    elif key == 'sku':
        qd.pop('sku', None)
    else:
        values = [v for v in qd.getlist(key) if v != slug]
        if hasattr(qd, 'setlist'):
            qd.setlist(key, values)
        else:
            qd.pop(key, None)
            for v in values:
                qd.appendlist(key, v)
    return qd.urlencode()
