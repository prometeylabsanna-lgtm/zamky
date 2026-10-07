"""Checkout helpers: money format and language-aware plurals."""

from decimal import Decimal, InvalidOperation

from pages.i18n_lib import plural_goods, plural_positions, tr

__all__ = [
    'format_uah',
    'plural_goods',
    'plural_positions',
    'COLOR_SWATCH',
    'delivery_meta',
    'payment_meta',
    'get_delivery_meta',
    'get_payment_meta',
]


def format_uah(value):
    try:
        n = int(Decimal(value))
    except (InvalidOperation, TypeError, ValueError):
        n = 0
    return f'{n:,}'.replace(',', ' ') + ' ₴'


COLOR_SWATCH = {
    'G': 'var(--swatch-brass)',
    'N': 'var(--swatch-nickel)',
    'B': 'var(--swatch-black)',
}


def delivery_meta():
    return {
        'np': {
            'note': tr('Відділення або поштомат · 1–2 дні'),
            'addr_label': tr('Відділення / поштомат'),
            'addr_ph': tr('№ відділення'),
        },
        'courier': {
            'note': tr('В день замовлення'),
            'addr_label': tr('Адреса'),
            'addr_ph': tr('Вулиця, будинок, квартира'),
        },
        'pickup': {
            'note': tr('З магазину в Києві · сьогодні'),
            'addr_label': '',
            'addr_ph': '',
        },
    }


def payment_meta():
    return {
        'card': {'note': 'Visa, Mastercard, Apple Pay, Google Pay'},
        'cod': {'note': tr('Оплата при отриманні')},
        'invoice': {'note': tr('Рахунок для юридичних осіб')},
    }


get_delivery_meta = delivery_meta
get_payment_meta = payment_meta
