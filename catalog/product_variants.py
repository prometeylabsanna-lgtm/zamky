from django.db.models import Prefetch
from django.urls import reverse

from pages.i18n_lib import tr

from .models import Product, ProductImage

COLOR_ORDER = {'G': 0, 'N': 1, 'B': 2}


def variant_payload(product):
    imgs = [
        {'src': img.image.url, 'alt': img.alt or product.name}
        for img in product.images.all()
        if img.image
    ]
    return {
        'id': product.pk,
        'sku': product.sku,
        'slug': product.slug,
        'url': product.get_absolute_url(),
        'name': tr(product.name),
        'price': int(product.price),
        'old_price': int(product.old_price) if product.old_price else None,
        'discount': product.discount_percent,
        'stock': int(product.stock or 0),
        'status': product.stock_status,
        'badge': product.stock_label,
        'stock_note': product.stock_note,
        'color': product.color_code or '',
        'color_label': tr(product.color_label),
        'size': product.size_mm or 0,
        'size_a': product.size_a,
        'size_b': product.size_b,
        'size_label': product.size_label,
        'cover': tr(product.cover),
        'images': imgs,
        'add_url': reverse('cart:add', kwargs={'pk': product.pk}),
        'quick_url': reverse('orders:quick', kwargs={'pk': product.pk}),
        'wishlist_url': reverse('cart:wishlist', kwargs={'pk': product.pk}),
    }


def _swatch_urls(family):
    if family is None:
        return {}
    urls = {}
    for row in family.color_swatches.all():
        if not row.image:
            continue
        try:
            urls[row.color_code] = row.image.url
        except ValueError:
            continue
    return urls


def _product_swatch_img(product):
    primary = product.images.first()
    if not primary or not primary.image:
        return ''
    try:
        return primary.image.url
    except ValueError:
        return ''


def _family_products(product):
    return (
        Product.objects.filter(is_active=True, family=product.family)
        .select_related('family')
        .prefetch_related(
            Prefetch(
                'images', queryset=ProductImage.objects.order_by('sort_order', 'id')
            ),
            'family__color_swatches',
        )
        .order_by('size_mm', 'color_code')
    )


def build_variant_context(product):
    """Колір і розмір з картки навіть без сім’ї варіантів."""
    in_family = bool(product.family_id)
    qs = _family_products(product) if in_family else [product]
    swatches = _swatch_urls(product.family) if in_family else {}
    variants = []
    seen_colors = {}
    seen_sizes = {}
    for item in qs:
        variants.append(variant_payload(item))
        if item.color_code and item.color_code not in seen_colors:
            seen_colors[item.color_code] = {
                'code': item.color_code,
                'label': tr(item.color_label),
                'img': swatches.get(item.color_code, '') or _product_swatch_img(item),
            }
        if item.size_mm and item.size_mm not in seen_sizes:
            seen_sizes[item.size_mm] = {
                'len': item.size_mm,
                'a': item.size_a,
                'b': item.size_b,
                'label': item.size_label,
            }
    colors = sorted(seen_colors.values(), key=lambda x: COLOR_ORDER.get(x['code'], 99))
    sizes = sorted(seen_sizes.values(), key=lambda x: x['len'])
    return variants, colors, sizes
