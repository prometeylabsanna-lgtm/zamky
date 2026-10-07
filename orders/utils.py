"""Checkout helpers: money format and Ukrainian plurals."""

from decimal import Decimal, InvalidOperation


def format_uah(value):
    try:
        n = int(Decimal(value))
    except (InvalidOperation, TypeError, ValueError):
        n = 0
    return f'{n:,}'.replace(',', ' ') + ' ₴'


def plural_positions(n):
    """1 позиція / 2 позиції / 5 позицій."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    a, b = n % 10, n % 100
    if a == 1 and b != 11:
        return 'позиція'
    if 2 <= a <= 4 and (b < 12 or b > 14):
        return 'позиції'
    return 'позицій'


def plural_goods(n):
    """1 товар / 2 товари / 5 товарів (як у дизайні Checkout.dc.html)."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    a, b = n % 10, n % 100
    if a == 1 and b != 11:
        return 'товар'
    if 2 <= a <= 4 and (b < 12 or b > 14):
        return 'товари'
    return 'товарів'


COLOR_SWATCH = {
    'G': 'var(--swatch-brass)',
    'N': 'var(--swatch-nickel)',
    'B': 'var(--swatch-black)',
}

DELIVERY_META = {
    'np': {
        'note': 'Відділення або поштомат · 1–2 дні',
        'addr_label': 'Відділення / поштомат',
        'addr_ph': '№ відділення',
    },
    'courier': {
        'note': 'В день замовлення',
        'addr_label': 'Адреса',
        'addr_ph': 'Вулиця, будинок, квартира',
    },
    'pickup': {
        'note': 'З магазину в Києві · сьогодні',
        'addr_label': '',
        'addr_ph': '',
    },
}

PAYMENT_META = {
    'card': {'note': 'Visa, Mastercard, Apple Pay, Google Pay'},
    'cod': {'note': 'Оплата при отриманні'},
    'invoice': {'note': 'Рахунок для юридичних осіб'},
}
