from catalog.filter_i18n import localized_text

MEASURE_TITLE_UA = 'Як виміряти циліндр?'
MEASURE_TITLE_RU = 'Как измерить цилиндр?'
MEASURE_TEXT_UA = (
    'Виміряйте відстань від центру отвору під кріпильний гвинт до зовнішнього (A) '
    'і внутрішнього (B) краю дверного полотна разом з накладками. '
    'Сума A і B — загальна довжина циліндра.'
)
MEASURE_TEXT_RU = (
    'Измерьте расстояние от центра отверстия под крепёжный винт до внешнего (A) '
    'и внутреннего (B) края дверного полотна вместе с накладками. '
    'Сумма A и B — общая длина цилиндра.'
)


def _chain(category):
    node = category
    seen = set()
    while node is not None:
        pk = getattr(node, 'pk', None)
        if pk in seen:
            break
        if pk is not None:
            seen.add(pk)
        yield node
        node = getattr(node, 'parent', None)


def _first_localized(category, ua_attr, ru_attr):
    for node in _chain(category):
        ua = (getattr(node, ua_attr, None) or '').strip()
        if ua:
            return localized_text(ua, getattr(node, ru_attr, '') or '')
    return ''


def resolve_measure(category):
    if category is None:
        return '', ''
    title = _first_localized(category, 'measure_title', 'measure_title_ru')
    text = _first_localized(category, 'measure_text', 'measure_text_ru')
    if title and text:
        return title, text
    return '', ''


def apply_default_measure(category):
    changed = []
    if not (category.measure_title or '').strip():
        category.measure_title = MEASURE_TITLE_UA
        changed.append('measure_title')
    if not (category.measure_title_ru or '').strip():
        category.measure_title_ru = MEASURE_TITLE_RU
        changed.append('measure_title_ru')
    if not (category.measure_text or '').strip():
        category.measure_text = MEASURE_TEXT_UA
        changed.append('measure_text')
    if not (category.measure_text_ru or '').strip():
        category.measure_text_ru = MEASURE_TEXT_RU
        changed.append('measure_text_ru')
    return changed
