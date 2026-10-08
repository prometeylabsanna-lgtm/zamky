from django.utils.functional import lazy
from django.utils.translation import get_language

from pages.translations import RU_MAP

# Longer phrases first — for product titles / mixed DB strings.
PHRASE_RU = (
    ('латунь полірована', 'латунь полированная'),
    ('Полірована латунь', 'Полированная латунь'),
    ('полірована латунь', 'полированная латунь'),
    ('Матовий нікель', 'Матовый никель'),
    ('матовий нікель', 'матовый никель'),
    ('нікель сатин', 'никель сатин'),
    ('Чорне матове', 'Чёрное матовое'),
    ('чорне матове', 'чёрное матовое'),
    ('чорний матовий', 'чёрный матовый'),
    ('Чорний матовий', 'Чёрный матовый'),
    ('половинчастий', 'половинчатый'),
    ('Половинчастий', 'Половинчатый'),
    ('ключ/тумблер', 'ключ/тумблер'),
    ('Ключ / тумблер', 'Ключ / тумблер'),
    ('Ключ / ключ', 'Ключ / ключ'),
    ('Циліндровий механізм', 'Цилиндровый механизм'),
    ('циліндровий механізм', 'цилиндровый механизм'),
    ('Циліндр', 'Цилиндр'),
    ('циліндр', 'цилиндр'),
    ('ключів', 'ключей'),
    ('ключі', 'ключи'),
    ('Ключі', 'Ключи'),
    ('Туреччина', 'Турция'),
    ('Італія', 'Италия'),
    ('Китай', 'Китай'),
    ('Латунь', 'Латунь'),
    ('Нікель', 'Никель'),
    ('Чорний', 'Чёрный'),
    ('Так', 'Да'),
)


def tr(text):
    if text is None:
        return text
    if not isinstance(text, str):
        return text
    lang = (get_language() or 'ua')[:2]
    if lang != 'ru':
        return text
    mapped = RU_MAP.get(text)
    if mapped is not None:
        return mapped
    out = text
    for src, dst in PHRASE_RU:
        if src in out:
            out = out.replace(src, dst)
    return out


tr_lazy = lazy(tr, str)


def site_lang_code():
    lang = (get_language() or 'ua')[:2]
    return 'RU' if lang == 'ru' else 'UA'


def plural_goods(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    a, b = n % 10, n % 100
    lang = (get_language() or 'ua')[:2]
    if lang == 'ru':
        if a == 1 and b != 11:
            return 'товар'
        if 2 <= a <= 4 and (b < 12 or b > 14):
            return 'товара'
        return 'товаров'
    if a == 1 and b != 11:
        return 'товар'
    if 2 <= a <= 4 and (b < 12 or b > 14):
        return 'товари'
    return 'товарів'


def plural_positions(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    a, b = n % 10, n % 100
    lang = (get_language() or 'ua')[:2]
    if lang == 'ru':
        if a == 1 and b != 11:
            return 'позиция'
        if 2 <= a <= 4 and (b < 12 or b > 14):
            return 'позиции'
        return 'позиций'
    if a == 1 and b != 11:
        return 'позиція'
    if 2 <= a <= 4 and (b < 12 or b > 14):
        return 'позиції'
    return 'позицій'


JS_I18N_KEYS = (
    'Надсилаємо…',
    'Сортування:',
    'Адреса',
    'Безкоштовно',
    'Фото',
    'Код товару:',
    'немає',
    'мм',
    'Немає в наявності',
    'До кошика',
    'Скопійовано',
    'Додано до кошика',
    'Замовити',
    'Менеджер передзвонить протягом 15 хвилин і уточнить деталі замовлення.',
    'Поле обовʼязкове для заповнення',
    'Імʼя не може містити цифри або спецсимволи. Будь ласка, використовуйте лише букви',
    'Вкажіть імʼя (мінімум 2 літери)',
    'Введіть коректний номер мобільного телефону у форматі +380 (XX) XXX-XX-XX',
    'Некоректний формат email',
    'Напишіть хоча б кілька слів (від 10 символів)',
    'Потрібна згода на обробку даних',
    'Вкажіть місто.',
    'Вкажіть адресу або відділення.',
)


def js_i18n_dict():
    return {key: tr(key) for key in JS_I18N_KEYS}
