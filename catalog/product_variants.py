from django.urls import reverse

from pages.i18n_lib import tr

from .models import ProductImage


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


def _product_swatch_img(product):
    primary = product.images.first()
    if not primary or not primary.image:
        return ''
    try:
        return primary.image.url
    except ValueError:
        return ''


def build_variant_context(product):
    """Власний колір і розмір цього товару — без перемикання на інші артикули."""
    payload = variant_payload(product)
    colors = []
    sizes = []
    if product.color_code:
        colors.append(
            {
                'code': product.color_code,
                'label': tr(product.color_label),
                'img': _product_swatch_img(product),
            }
        )
    if product.size_mm:
        sizes.append(
            {
                'len': product.size_mm,
                'a': product.size_a,
                'b': product.size_b,
                'label': product.size_label,
            }
        )
    return [payload], colors, sizes
