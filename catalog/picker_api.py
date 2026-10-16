"""JSON API для підбору товарів (Design-v2 picker)."""

from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.http import JsonResponse
from django.templatetags.static import static
from django.urls import reverse
from django.views import View

from catalog.models import AttributeValue, Product

DOOR_CATEGORY_HINTS = {
    '0': ['Замки', 'захист'],
    '1': ['Серцевини', 'циліндр'],
    '2': ['Замки', 'захист'],
    '3': ['Серцевини'],
    '4': ['код', 'елект'],
    'entrance': ['Замки', 'захист'],
    'interior': ['Серцевини', 'циліндр'],
    'metal': ['Замки', 'захист'],
    'plastic': ['Серцевини'],
    'metal_electric': ['код', 'елект'],
}


def _catalog_qs():
    return Product.objects.filter(is_active=True, catalog_order__lt=500).exclude(
        sku__startswith='HOME-'
    )


def _door_filter(qs, raw):
    if not raw:
        return qs
    hints = DOOR_CATEGORY_HINTS.get(raw.strip().lower())
    if hints is None and raw.isdigit():
        hints = DOOR_CATEGORY_HINTS.get(raw)
    if not hints:
        return qs
    q = Q()
    for hint in hints:
        q |= Q(category__name__icontains=hint) | Q(category__parent__name__icontains=hint)
    return qs.filter(q)


def _filter_attr(qs, slug, value):
    if not value:
        return qs
    values = [v.strip() for v in value.split(',') if v.strip()]
    if not values:
        return qs
    return qs.filter(
        attributes__slug__in=values,
        attributes__attribute__slug=slug,
    )


def _filter_brand(qs, raw):
    if not raw:
        return qs
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    q = Q()
    for part in parts:
        q |= Q(brand__iexact=part) | Q(brand__icontains=part)
        av = AttributeValue.objects.filter(
            attribute__slug='brand',
            slug__iexact=part,
        ).first()
        if av:
            q |= Q(attributes=av)
    return qs.filter(q)


def _filter_size(qs, raw):
    if not raw:
        return qs
    raw = raw.strip()
    if 'x' in raw.lower() or '×' in raw:
        sep = '×' if '×' in raw else 'x'
        left, _, right = raw.lower().partition(sep)
        try:
            a, b = int(left.strip()), int(right.strip())
            return qs.filter(size_a=a, size_b=b)
        except ValueError:
            pass
    try:
        mm = int(raw)
        return qs.filter(Q(size_mm=mm) | Q(size_a=mm) | Q(size_b=mm))
    except ValueError:
        return qs.filter(
            Q(color_label__icontains=raw)
            | Q(finish__icontains=raw)
            | Q(cover__icontains=raw)
        )


def _picker_item(product):
    img = product.primary_image
    image_url = img.image.url if img else static('img/product-brass.png')
    old = product.old_price
    return {
        'id': product.pk,
        'name': product.name,
        'slug': product.slug,
        'url': reverse('catalog:product', kwargs={'slug': product.slug}),
        'image': image_url,
        'price': product.price_display,
        'price_raw': str(product.price.quantize(Decimal('0.01'))),
        'old_price': product.old_price_display if old and old > product.price else '',
        'brand': product.brand,
        'in_stock': product.stock_status != 'out',
        'stock_label': product.stock_label,
        'add_url': reverse('cart:add', kwargs={'pk': product.pk}),
    }


class PickerApiView(View):
    def get(self, request):
        qs = _catalog_qs()
        qs = _door_filter(qs, request.GET.get('door', ''))
        qs = _filter_brand(qs, request.GET.get('brand', ''))
        qs = _filter_attr(qs, 'color', request.GET.get('color', ''))
        qs = _filter_attr(qs, 'mech', request.GET.get('mech', ''))
        qs = _filter_size(qs, request.GET.get('size', ''))

        price_raw = request.GET.get('price', '').strip()
        if price_raw:
            qs = self._filter_price_band(qs, price_raw)

        products = qs.distinct().prefetch_related('images').order_by('catalog_order', 'name')[:24]
        items = [_picker_item(p) for p in products]
        return JsonResponse({'ok': True, 'count': len(items), 'items': items})

    def _filter_price_band(self, qs, label):
        bands = {
            'до 1500 ₴': (0, 1500),
            '1500 – 3000 ₴': (1500, 3000),
            '3000 – 4500 ₴': (3000, 4500),
            'від 4500 ₴': (4500, None),
        }
        lo_hi = bands.get(label)
        if not lo_hi:
            if '-' in label:
                parts = label.replace('₴', '').replace(' ', '').split('-')
                try:
                    lo_hi = (Decimal(parts[0]), Decimal(parts[1]))
                except (InvalidOperation, IndexError):
                    return qs
            else:
                return qs
        lo, hi = lo_hi
        qs = qs.filter(price__gte=lo)
        if hi is not None:
            qs = qs.filter(price__lt=hi)
        return qs
