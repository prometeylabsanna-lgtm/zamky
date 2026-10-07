from decimal import Decimal

from django.db import transaction
from django.db.models import F

from cart.services import CartService
from catalog.models import Product

from .models import Order, OrderItem

DELIVERY_PRICES = {
    Order.DeliveryMethod.NP: Decimal('80'),
    Order.DeliveryMethod.COURIER: Decimal('150'),
    Order.DeliveryMethod.PICKUP: Decimal('0'),
}


class CheckoutError(Exception):
    pass


@transaction.atomic
def create_order_from_cart(request, cleaned_data, idempotency_key):
    existing = Order.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
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
    delivery_price = DELIVERY_PRICES.get(delivery_method, Decimal('0'))
    subtotal = sum((item['line_total'] for item in items), Decimal('0'))

    order = Order.objects.create(
        first_name=cleaned_data['first_name'],
        last_name=cleaned_data.get('last_name', ''),
        phone=cleaned_data['phone'],
        email=cleaned_data.get('email', ''),
        district=cleaned_data.get('district'),
        delivery_method=delivery_method,
        payment_method=cleaned_data['payment_method'],
        address=cleaned_data.get('address', ''),
        comment=cleaned_data.get('comment', ''),
        subtotal=subtotal,
        delivery_price=delivery_price,
        total=subtotal + delivery_price,
        idempotency_key=idempotency_key,
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

    cart.clear()
    return order, True
