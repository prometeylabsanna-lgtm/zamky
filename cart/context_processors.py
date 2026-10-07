from .services import CartService, WishlistService


def cart_context(request):
    cart = CartService(request)
    wishlist = WishlistService(request)
    return {
        'cart_count': cart.total_quantity(),
        'cart_items': cart.items(),
        'cart_subtotal': cart.subtotal(),
        'wishlist_count': wishlist.count(),
        'wishlist_ids': set(wishlist.items_ids),
    }
