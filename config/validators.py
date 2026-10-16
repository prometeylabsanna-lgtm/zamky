"""Спільна серверна валідація імені та UA-телефона."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError

from pages.i18n_lib import tr

NAME_RE = re.compile(
    r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ'ʼ'`’\- ]+$",
    re.UNICODE,
)
UA_PHONE_RE = re.compile(r'^\+380\d{9}$')

MSG_REQUIRED = 'Поле обовʼязкове для заповнення'
MSG_NAME = (
    'Імʼя не може містити цифри або спецсимволи. '
    'Будь ласка, використовуйте лише букви'
)
MSG_NAME_SHORT = 'Вкажіть імʼя (мінімум 2 літери)'
MSG_PHONE = 'Введіть номер у форматі +38 (0XX) XXX XX XX'
MSG_EMAIL = 'Некоректний формат email'
MSG_MESSAGE = 'Напишіть хоча б кілька слів (від 10 символів)'
MSG_CONSENT = 'Потрібна згода на обробку даних'


def normalize_ua_phone(value: str) -> str | None:
    digits = re.sub(r'\D+', '', value or '')
    if digits.startswith('380') and len(digits) == 12:
        phone = '+' + digits
    elif digits.startswith('0') and len(digits) == 10:
        phone = '+38' + digits
    elif len(digits) == 9:
        phone = '+380' + digits
    else:
        return None
    if not UA_PHONE_RE.match(phone):
        return None
    return phone


def clean_ua_phone(value: str, *, required: bool = True) -> str:
    raw = (value or '').strip()
    if not raw:
        if required:
            raise ValidationError(tr(MSG_REQUIRED))
        return ''
    phone = normalize_ua_phone(raw)
    if not phone:
        raise ValidationError(tr(MSG_PHONE))
    return phone


def clean_person_name(value: str, *, required: bool = True) -> str:
    name = (value or '').strip()
    if not name:
        if required:
            raise ValidationError(tr(MSG_REQUIRED))
        return ''
    if len(name) < 2:
        raise ValidationError(tr(MSG_NAME_SHORT))
    if re.search(r'\d', name) or not NAME_RE.match(name):
        raise ValidationError(tr(MSG_NAME))
    return re.sub(r'\s+', ' ', name)
