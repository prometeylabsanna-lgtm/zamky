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


def cms_checkout(key: str) -> str:
    from pages.cms_content import get_block_text
    from pages.i18n_lib import site_lang_code

    return get_block_text('checkout', key, lang=site_lang_code())


def cms_price(key: str, fallback: str) -> Decimal:
    raw = (cms_checkout(key) or fallback).replace(' ', '').replace(',', '.')
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return Decimal(fallback)


def delivery_meta():
    return {
        'np': {
            'title': cms_checkout('ship_np'),
            'note': cms_checkout('ship_np_note'),
            'addr_label': cms_checkout('ship_np_addr'),
            'addr_ph': cms_checkout('ship_np_addr_ph'),
            'price': cms_price('ship_np_price', '80'),
        },
        'courier': {
            'title': cms_checkout('ship_courier'),
            'note': cms_checkout('ship_courier_note'),
            'addr_label': cms_checkout('ship_courier_addr'),
            'addr_ph': cms_checkout('ship_courier_addr_ph'),
            'price': cms_price('ship_courier_price', '150'),
        },
        'pickup': {
            'title': cms_checkout('ship_pickup'),
            'note': cms_checkout('ship_pickup_note'),
            'addr_label': '',
            'addr_ph': '',
            'price': cms_price('ship_pickup_price', '0'),
        },
    }


def payment_meta():
    return {
        'card': {
            'title': cms_checkout('pay_card'),
            'note': cms_checkout('pay_card_note'),
        },
        'cod': {
            'title': cms_checkout('pay_cod'),
            'note': cms_checkout('pay_cod_note'),
        },
        'invoice': {
            'title': cms_checkout('pay_invoice'),
            'note': cms_checkout('pay_invoice_note'),
        },
    }


get_delivery_meta = delivery_meta
get_payment_meta = payment_meta
