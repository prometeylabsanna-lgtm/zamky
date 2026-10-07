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
        subtotal = cart.subtotal()
        context = {
            'cart_count': cart.total_quantity(),
            'cart_items': cart.items(),
            'cart_subtotal': subtotal,
            'cart_error': error,
        }
        if request.headers.get('HX-Request') == 'true':
            page = request.POST.get('page')
            if page in {'checkout', 'cart'}:
                if page == 'checkout':
                    delivery_method = request.POST.get('delivery_method') or Order.DeliveryMethod.NP
                    delivery_price = DELIVERY_PRICES.get(
                        delivery_method, DELIVERY_PRICES[Order.DeliveryMethod.NP]
                    )
                    context.update(
                        {
                            'page': 'checkout',
                            'step': 'checkout',
                            'delivery_price': delivery_price,
                            'order_total': subtotal + delivery_price,
                        }
                    )
                else:
                    context.update({'page': 'cart', 'step': 'cart'})
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
        }
        if request.headers.get('HX-Request') == 'true':
            return render(request, 'cart/partials/wishlist_btn.html', context)
        return redirect(request.META.get('HTTP_REFERER') or '/')


class CartBadgeView(View):
    def get(self, request):
        cart = CartService(request)
        return render(
            request,
            'cart/partials/badge.html',
            {'cart_count': cart.total_quantity()},
        )
