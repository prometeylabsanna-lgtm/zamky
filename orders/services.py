from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from cart.services import CartService
from catalog.models import Product

from .models import Order, OrderItem
from .payments import online_payment_enabled

def delivery_prices():
    from .utils import cms_price

    return {
        Order.DeliveryMethod.NP: cms_price('ship_np_price', '80'),
        Order.DeliveryMethod.COURIER: cms_price('ship_courier_price', '150'),
        Order.DeliveryMethod.PICKUP: cms_price('ship_pickup_price', '0'),
    }


class CheckoutError(Exception):
    pass


def create_order_from_cart(request, cleaned_data, idempotency_key):
    existing = Order.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        _clear_cart(request)
        return existing, False
    try:
        return _create_order_from_cart(request, cleaned_data, idempotency_key)
    except IntegrityError:
        existing = Order.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            _clear_cart(request)
            return existing, False
        raise


def _clear_cart(request):
    CartService(request).clear()


@transaction.atomic
def _create_order_from_cart(request, cleaned_data, idempotency_key):
    existing = Order.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        _clear_cart(request)
        return existing, False

    cart = CartService(request)
    raw = getattr(cart, 'cart', {}) or {}
    if not raw:
        raise CheckoutError('Кошик порожній.')

    product_ids = [int(k) for k in raw.keys()]
    locked = {
        p.pk: p
        for p in Product.objects.select_for_update().filter(pk__in=product_ids, is_active=True)
    }

    items = []
    for key, data in raw.items():
        product = locked.get(int(key))
        qty = int(data.get('qty', 0))
        if not product:
            raise CheckoutError('Товар у кошику більше недоступний.')
        if qty < 1:
            continue
        if qty > product.stock:
            raced = Order.objects.filter(idempotency_key=idempotency_key).first()
            if raced:
                _clear_cart(request)
                return raced, False
            raise CheckoutError(
                f'Недостатньо залишку для «{product.name}»: доступно {product.stock} шт.'
            )
        items.append(
            {
                'product': product,
                'quantity': qty,
                'line_total': product.price * qty,
            }
        )
    if not items:
        raise CheckoutError('Кошик порожній.')

    delivery_method = cleaned_data['delivery_method']
    delivery_price = delivery_prices().get(delivery_method, Decimal('0'))
    subtotal = sum((item['line_total'] for item in items), Decimal('0'))
    payment_method = cleaned_data['payment_method']
    card_online = payment_method == Order.PaymentMethod.CARD and online_payment_enabled()
    if card_online:
        status = Order.Status.AWAITING_PAYMENT
        minutes = int(getattr(settings, 'PAYMENT_RESERVE_MINUTES', 30) or 30)
        reserved_until = timezone.now() + timedelta(minutes=minutes)
    else:
        status = Order.Status.NEW
        reserved_until = None

    city = (cleaned_data.get('city') or '').strip()[:120]
    address = (cleaned_data.get('address') or '').strip()[:300]

    order = Order.objects.create(
        first_name=cleaned_data['first_name'],
        last_name=cleaned_data.get('last_name', ''),
        phone=cleaned_data['phone'],
        email=cleaned_data.get('email', ''),
        city=city,
        delivery_method=delivery_method,
        payment_method=payment_method,
        address=address,
        np_city_ref=(cleaned_data.get('np_city_ref') or '')[:36],
        np_warehouse_ref=(cleaned_data.get('np_warehouse_ref') or '')[:36],
        np_warehouse_snapshot=(cleaned_data.get('np_warehouse_snapshot') or '')[:300],
        comment=cleaned_data.get('comment', ''),
        subtotal=subtotal,
        delivery_price=delivery_price,
        total=subtotal + delivery_price,
        idempotency_key=idempotency_key,
        status=status,
        reserved_until=reserved_until,
    )

    for item in items:
        product = locked[item['product'].pk]
        updated = Product.objects.filter(pk=product.pk, stock__gte=item['quantity']).update(
            stock=F('stock') - item['quantity']
        )
        if not updated:
            raise CheckoutError(f'Не вдалося списати залишок для «{product.name}».')
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            sku=product.sku,
            unit_price=product.price,
            quantity=item['quantity'],
            line_total=item['line_total'],
        )

    if card_online:
        from .payments import create_payment

        create_payment(order)

    cart.clear()
    return order, True
