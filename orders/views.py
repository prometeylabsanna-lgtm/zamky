import re
import uuid

from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, FormView

from cart.services import CartService
from catalog.models import Product

from .forms import CheckoutForm
from .models import DeliveryDistrict, Order, QuickOrder
from .services import CheckoutError, DELIVERY_PRICES, create_order_from_cart


class SetDistrictView(View):
    def post(self, request):
        slug = request.POST.get('slug', '').strip()
        if slug:
            district = DeliveryDistrict.objects.filter(slug=slug, is_active=True).first()
            if district:
                request.session['district_slug'] = district.slug
            else:
                request.session.pop('district_slug', None)
        else:
            request.session.pop('district_slug', None)
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
        if request.headers.get('HX-Request') == 'true':
            response = render(request, 'partials/district_label.html', {})
            response['HX-Redirect'] = next_url
            return response
        return redirect(next_url)


class CheckoutView(FormView):
    template_name = 'orders/checkout.html'
    form_class = CheckoutForm

    def dispatch(self, request, *args, **kwargs):
        self.cart = CartService(request)
        self.step = request.GET.get('step', 'cart')
        if self.step not in {'cart', 'checkout', 'done'}:
            self.step = 'cart'
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['idempotency_key'] = self.request.session.get('checkout_idempotency') or uuid.uuid4().hex
        self.request.session['checkout_idempotency'] = initial['idempotency_key']
        slug = self.request.session.get('district_slug')
        if slug:
            district = DeliveryDistrict.objects.filter(slug=slug, is_active=True).first()
            if district:
                initial['district'] = district.pk
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        items = self.cart.items()
        subtotal = self.cart.subtotal()
        delivery_method = self.request.POST.get('delivery_method') or self.request.GET.get(
            'delivery', Order.DeliveryMethod.NP
        )
        delivery_price = DELIVERY_PRICES.get(delivery_method, DELIVERY_PRICES[Order.DeliveryMethod.NP])
        order = None
        if self.step == 'done':
            order_id = self.request.session.get('last_order_id')
            if order_id:
                order = Order.objects.prefetch_related('items').filter(pk=order_id).first()
        ctx.update(
            {
                'cart_items': items,
                'cart_subtotal': subtotal,
                'delivery_price': delivery_price,
                'order_total': subtotal + delivery_price,
                'step': self.step if items or self.step == 'done' else 'cart',
                'is_empty': not items and self.step != 'done',
                'order': order,
                'delivery_choices': Order.DeliveryMethod.choices,
                'payment_choices': Order.PaymentMethod.choices,
                'delivery_prices': DELIVERY_PRICES,
            }
        )
        return ctx

    def form_valid(self, form):
        key = form.cleaned_data['idempotency_key']
        try:
            order, created = create_order_from_cart(self.request, form.cleaned_data, key)
        except CheckoutError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        self.request.session['last_order_id'] = order.pk
        self.request.session.pop('checkout_idempotency', None)
        if self.request.headers.get('HX-Request') == 'true':
            return redirect(f"{reverse('orders:checkout')}?step=done")
        return redirect(f"{reverse('orders:checkout')}?step=done")

    def form_invalid(self, form):
        self.step = 'checkout'
        return super().form_invalid(form)


class OrderSuccessView(DetailView):
    model = Order
    template_name = 'orders/success.html'
    context_object_name = 'order'
    slug_field = 'number'
    slug_url_kwarg = 'number'


class QuickOrderView(View):
    phone_re = re.compile(r'^[\d\s\-\+\(\)]{9,20}$')

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_active=True)
        raw = (request.POST.get('phone') or '').strip()
        digits = re.sub(r'\D', '', raw)
        if digits.startswith('380') and len(digits) >= 12:
            phone = '+' + digits
        elif len(digits) == 9:
            phone = '+380' + digits
        elif len(digits) == 10 and digits.startswith('0'):
            phone = '+38' + digits
        else:
            phone = raw if raw.startswith('+') else ('+380' + digits if digits else '')
        if not digits or len(digits) < 9 or not self.phone_re.match(phone or raw):
            context = {'error': 'Вкажіть коректний телефон', 'product': product}
            if request.headers.get('HX-Request') == 'true':
                return render(request, 'orders/partials/quick_order_form.html', context)
            return HttpResponseBadRequest(context['error'])
        try:
            qty = max(1, int(request.POST.get('quantity', 1)))
        except (TypeError, ValueError):
            qty = 1
        QuickOrder.objects.create(
            product=product,
            phone=phone,
            name=(request.POST.get('name') or '').strip(),
            quantity=qty,
        )
        if request.headers.get('HX-Request') == 'true':
            return render(request, 'orders/partials/quick_order_done.html', {'product': product})
        return redirect(product.get_absolute_url())
