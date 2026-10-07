from django import template

from pages.i18n_lib import tr

register = template.Library()


@register.filter(name='tr')
def tr_filter(value):
    if value is None:
        return value
    return tr(str(value))


@register.simple_tag(name='t')
def t_tag(text):
    return tr(text)
