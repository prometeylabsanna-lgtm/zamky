import hashlib
import hmac
import json
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from catalog.models import Product

from .models import Order


class PaymentError(Exception):
    pass


def online_payment_enabled():
    return bool(getattr(settings, 'PAYMENT_STUB_ENABLED', False)) or bool(
        getattr(settings, 'PAYMENT_ONLINE_ENABLED', False)
    )


def create_payment(order):
    if order.payment_method != Order.PaymentMethod.CARD:
        return order
    if order.payment_ref:
        return order
    order.payment_ref = uuid.uuid4().hex
    order.save(update_fields=['payment_ref', 'updated_at'])
    return order


def sign_payload(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()


def webhook_secret() -> str:
    return str(getattr(settings, 'PAYMENT_WEBHOOK_SECRET', '') or '')


def verify_webhook(request) -> dict:
    secret = webhook_secret()
    if not secret:
        raise PaymentError('missing secret')
    signature = request.headers.get('X-Payment-Signature') or ''
    expected = sign_payload(request.body or b'', secret)
    if not hmac.compare_digest(str(signature), expected):
        raise PaymentError('bad signature')
    try:
        payload = json.loads((request.body or b'').decode('utf-8') or '{}')
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PaymentError('bad json') from exc
    if not isinstance(payload, dict):
        raise PaymentError('bad json')
    return payload


@transaction.atomic
def mark_order_paid(*, number: str, payment_ref: str = ''):
    order = (
        Order.objects.select_for_update()
        .filter(number=number)
        .first()
    )
    if not order:
        raise PaymentError('not found')
    ref = (payment_ref or '').strip()
    if order.payment_ref and (not ref or order.payment_ref != ref):
        raise PaymentError('ref mismatch')
    if order.status == Order.Status.PAID:
        return order, False
    if order.status != Order.Status.AWAITING_PAYMENT:
        return order, False
    order.status = Order.Status.PAID
    order.reserved_until = None
    if ref and not order.payment_ref:
        order.payment_ref = ref
    order.save(update_fields=['status', 'reserved_until', 'payment_ref', 'updated_at'])
    return order, True


def release_expired_payment_holds() -> int:
    now = timezone.now()
    ids = list(
        Order.objects.filter(
            status=Order.Status.AWAITING_PAYMENT,
            reserved_until__isnull=False,
            reserved_until__lt=now,
        ).values_list('pk', flat=True)
    )
    released = 0
    for pk in ids:
        if _release_one(pk):
            released += 1
    return released


@transaction.atomic
def _release_one(pk: int) -> bool:
    order = Order.objects.select_for_update().filter(pk=pk).first()
    if not order:
        return False
    if order.status != Order.Status.AWAITING_PAYMENT:
        return False
    if not order.reserved_until or order.reserved_until >= timezone.now():
        return False
    for item in order.items.all():
        if item.product_id:
            Product.objects.filter(pk=item.product_id).update(stock=F('stock') + item.quantity)
    order.status = Order.Status.CANCELLED
    order.reserved_until = None
    order.save(update_fields=['status', 'reserved_until', 'updated_at'])
    return True
