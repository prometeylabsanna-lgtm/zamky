"""JSON API для підбору товарів (Design-v2 picker)."""

from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.http import JsonResponse
from django.templatetags.static import static
from django.urls import reverse
from django.views import View

from catalog.models import AttributeValue, Product
from pages.picker_defaults import door_category_ids, door_hints, price_band


def _catalog_qs():
    return Product.objects.filter(is_active=True, catalog_order__lt=500).exclude(
        sku__startswith='HOME-'
    )


def _door_filter(qs, raw):
    if not raw:
        return qs
    cat_ids = door_category_ids(raw)
    if cat_ids:
        return qs.filter(category_id__in=cat_ids)
    hints = door_hints(raw)
    if not hints:
        return qs
    q = Q()
    for hint in hints:
        q |= Q(category__name__icontains=hint) | Q(category__parent__name__icontains=hint)
    matched = qs.filter(q)
    if matched.exists():
        return matched
    return qs


def _filter_attr(qs, slug, value):
    if not value:
        return qs
    values = [v.strip() for v in value.split(',') if v.strip()]
    if not values:
        return qs
    return qs.filter(
        Q(attributes__slug__in=values) | Q(attributes__value__in=values),
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


def _filter_price(qs, label):
    lo_hi = price_band(label)
    if lo_hi is None:
        if '-' in label:
            parts = label.replace('₴', '').replace(' ', '').split('-')
            try:
                lo_hi = (Decimal(parts[0]), Decimal(parts[1]))
            except (InvalidOperation, IndexError):
                return qs
        else:
            return qs
    lo, hi = lo_hi
    if lo is not None:
        qs = qs.filter(price__gte=lo)
    if hi is not None:
        qs = qs.filter(price__lt=hi)
    return qs


def _apply_picker_filters(request, qs):
    from pages.models_picker import PickerFilter

    special = {
        'brand': _filter_brand,
        'price': _filter_price,
        'size': _filter_size,
    }
    filters = PickerFilter.objects.filter(is_active=True).select_related('attribute')
    for filt in filters:
        raw = (request.GET.get(filt.key) or '').strip()
        if not raw:
            continue
        handler = special.get(filt.key)
        if handler is not None:
            qs = handler(qs, raw)
            continue
        slug = filt.attribute.slug if filt.attribute_id else filt.key
        qs = _filter_attr(qs, slug, raw)
    return qs


def _popular_products():
    from pages.popular_products import products_for_tab

    curated = products_for_tab('hits')
    if curated:
        return curated
    qs = _catalog_qs().prefetch_related('images')
    hits = qs.filter(is_hit=True).order_by('catalog_order', 'pk')
    if hits.exists():
        return list(hits[:8])
    return list(qs.order_by('catalog_order', 'name')[:8])


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
        qs = _apply_picker_filters(request, qs)

        products = list(
            qs.distinct().prefetch_related('images').order_by('catalog_order', 'name')[:24]
        )
        fallback = False
        if not products:
            products = list(_popular_products()[:8])
            fallback = bool(products)
        items = [_picker_item(p) for p in products]
        return JsonResponse(
            {
                'ok': True,
                'count': len(items),
                'items': items,
                'fallback': fallback,
            }
        )
