"""Локалізація назв і значень фільтрів (UA / RU)."""


def localized_text(ua, ru=''):
    from django.utils.translation import get_language

    from pages.i18n_lib import tr

    lang = (get_language() or 'ua')[:2]
    if lang == 'ru':
        custom = (ru or '').strip()
        if custom:
            return custom
        return tr(ua or '')
    return ua or ''


def fill_filter_translations(group_model=None, attr_model=None, value_model=None):
    from django.utils import translation

    from pages.i18n_lib import tr

    from .models import Attribute, AttributeGroup, AttributeValue

    group_model = group_model or AttributeGroup
    attr_model = attr_model or Attribute
    value_model = value_model or AttributeValue

    translation.activate('ru')
    try:
        _fill_name_ru(group_model, tr)
        _fill_name_ru(attr_model, tr)
        for obj in value_model.objects.all():
            current = (getattr(obj, 'value_ru', None) or '').strip()
            ru = current or tr(obj.value)
            if ru and ru != (obj.value_ru or ''):
                obj.value_ru = ru
                obj.save(update_fields=['value_ru'])
    finally:
        translation.deactivate()


def _fill_name_ru(model, tr):
    for obj in model.objects.all():
        current = (getattr(obj, 'name_ru', None) or '').strip()
        ru = current or tr(obj.name)
        if ru and ru != (obj.name_ru or ''):
            obj.name_ru = ru
            obj.save(update_fields=['name_ru'])
