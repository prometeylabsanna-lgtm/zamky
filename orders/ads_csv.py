import csv
from io import StringIO

from django.utils import timezone


def orders_ads_csv(orders) -> str:
    if hasattr(orders, 'prefetch_related'):
        orders = orders.prefetch_related('items')
    buf = StringIO()
    buf.write('\ufeff')
    writer = csv.writer(buf)
    writer.writerow(
        [
            'Імʼя',
            'Прізвище',
            'Телефон',
            'Email',
            'Місто',
            'Адреса',
            'Номер замовлення',
            'Дата',
            'Сума',
            'Товари',
        ]
    )
    for order in orders:
        items = '; '.join(f'{item.sku} × {item.quantity}' for item in order.items.all())
        created = timezone.localtime(order.created_at).strftime('%Y-%m-%d %H:%M')
        writer.writerow(
            [
                order.first_name,
                order.last_name,
                order.phone,
                order.email,
                order.city,
                order.address,
                order.number,
                created,
                f'{order.total:.2f}',
                items,
            ]
        )
    return buf.getvalue()
