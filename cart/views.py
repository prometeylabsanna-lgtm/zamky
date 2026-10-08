from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from catalog.models import Product
from orders.models import Order
from orders.services import DELIVERY_PRICES

from .services import CartError, CartService, WishlistService


class CartDrawerView(TemplateView):
    template_name = 'cart/partials/drawer.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cart = CartService(self.request)
        items = cart.items()
        ctx.update(
            {
                'cart_items': items,
                'cart_subtotal': cart.subtotal(),
                'cart_count': cart.total_quantity(),
            }
        )
        return ctx


class CartAddView(View):
    def post(self, request, pk):
        cart = CartService(request)
        try:
            cart.add(pk, quantity=int(request.POST.get('quantity', 1)))
            error = ''
        except CartError as exc:
            error = str(exc)
        return self._response(request, error)

    def _response(self, request, error=''):
        cart = CartService(request)
        context = {
            'cart_count': cart.total_quantity(),
            'cart_items': cart.items(),
            'cart_subtotal': cart.subtotal(),
            'cart_error': error,
        }
        if request.headers.get('HX-Request') == 'true':
            response = render(request, 'cart/partials/cart_oob.html', context)
            if error:
                response['HX-Retarget'] = '#cart-toast'
                response['HX-Reswap'] = 'innerHTML'
            return response
        if error:
            return HttpResponseBadRequest(error)
        return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or '/')


class CartUpdateView(View):
    def post(self, request, pk):
        cart = CartService(request)
        action = request.POST.get('action')
        try:
            if action == 'remove':
                cart.remove(pk)
            else:
                qty = request.POST.get('quantity')
                if action == 'inc':
                    item_qty = next(
                        (i['quantity'] for i in cart.items() if i['product'].pk == pk),
                        0,
                    )
                    cart.set_quantity(pk, item_qty + 1)
                elif action == 'dec':
                    item_qty = next(
                        (i['quantity'] for i in cart.items() if i['product'].pk == pk),
                        0,
                    )
                    cart.set_quantity(pk, item_qty - 1)
                elif qty is not None:
                    cart.set_quantity(pk, int(qty))
            error = ''
        except CartError as exc:
            error = str(exc)
        from decimal import Decimal

        items = cart.items()
        subtotal = cart.subtotal()
        subtotal_old = sum((item['old_total'] for item in items), Decimal('0'))
        savings = subtotal_old - subtotal
        if savings < 0:
            savings = Decimal('0')
        context = {
            'cart_count': cart.total_quantity(),
            'cart_items': items,
            'cart_subtotal': subtotal,
            'cart_subtotal_old': subtotal_old,
            'cart_savings': savings,
            'cart_qty_total': cart.total_quantity(),
            'cart_error': error,
        }
        if request.headers.get('HX-Request') == 'true':
            page = request.POST.get('page')
            if page in {'checkout', 'cart'}:
                delivery_method = request.POST.get('delivery_method') or Order.DeliveryMethod.NP
                delivery_price = DELIVERY_PRICES.get(
                    delivery_method, DELIVERY_PRICES[Order.DeliveryMethod.NP]
                )
                context.update(
                    {
                        'page': 'checkout',
                        'step': 'checkout',
                        'delivery_method': delivery_method,
                        'delivery_price': delivery_price,
                        'order_total': subtotal + delivery_price,
                        'oob_updates': True,
                    }
                )
                return render(request, 'orders/partials/checkout_items.html', context)
            return render(request, 'cart/partials/cart_oob.html', context)
        return redirect('orders:checkout')


class WishlistToggleView(View):
    def post(self, request, pk):
        get_object_or_404(Product, pk=pk, is_active=True)
        wishlist = WishlistService(request)
        added = wishlist.toggle(pk)
        context = {
            'product_id': pk,
            'in_wishlist': added,
            'wishlist_count': wishlist.count(),
            'swap_oob': True,
        }
        if request.headers.get('HX-Request') == 'true':
            variant = (request.POST.get('variant') or 'pdp').strip()
            if variant == 'card':
                return render(request, 'cart/partials/wishlist_card_btn.html', context)
            if variant == 'page' and not added:
                return render(request, 'cart/partials/wishlist_page_remove.html', context)
            return render(request, 'cart/partials/wishlist_btn.html', context)
        return redirect(request.META.get('HTTP_REFERER') or 'cart:wishlist_page')


class WishlistPageView(TemplateView):
    template_name = 'cart/wishlist.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        wishlist = WishlistService(self.request)
        products = wishlist.products()
        ctx.update(
            {
                'products': products,
                'wishlist_count': len(products),
                'wishlist_ids': {p.pk for p in products},
            }
        )
        return ctx


class CartBadgeView(View):
    def get(self, request):
        cart = CartService(request)
        return render(
            request,
            'cart/partials/badge.html',
            {'cart_count': cart.total_quantity()},
        )
