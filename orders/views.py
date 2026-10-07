import re
import uuid
from decimal import Decimal

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
from pages.i18n_lib import tr

from .utils import delivery_meta, format_uah, payment_meta


def build_checkout_steps(step):
    labels = [tr('Кошик'), tr('Оформлення'), tr('Готово')]
    if step == 'done':
        idx = 2
    elif step == 'cart':
        idx = 0
    else:
        idx = 1
    steps = []
    for i, label in enumerate(labels):
        if i < idx:
            state = 'is-done'
            n = '✓'
        elif i == idx:
            state = 'is-active'
            n = str(i + 1)
        else:
            state = 'is-todo'
            n = str(i + 1)
        steps.append({'label': label, 'n': n, 'state': state})
    return steps


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
        self.step = request.GET.get('step', 'checkout')
        if self.step not in {'cart', 'checkout', 'done'}:
            self.step = 'checkout'
        if self.step == 'cart' and self.cart.items():
            self.step = 'checkout'
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
        initial.setdefault('payment_method', Order.PaymentMethod.CARD)
        initial.setdefault('delivery_method', Order.DeliveryMethod.NP)
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        method = (
            form.data.get('delivery_method')
            if form.is_bound
            else form.initial.get('delivery_method', Order.DeliveryMethod.NP)
        )
        dmeta = delivery_meta()
        meta = dmeta.get(method, dmeta['np'])
        form.fields['address'].widget.attrs['placeholder'] = meta.get('addr_ph') or ''
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        items = self.cart.items()
        subtotal = self.cart.subtotal()
        qty_total = self.cart.total_quantity()
        subtotal_old = sum((item['old_total'] for item in items), Decimal('0'))
        savings = subtotal_old - subtotal
        if savings < 0:
            savings = Decimal('0')

        form = ctx.get('form')
        delivery_method = (
            (form.data.get('delivery_method') if form and form.is_bound else None)
            or self.request.POST.get('delivery_method')
            or self.request.GET.get('delivery')
            or Order.DeliveryMethod.NP
        )
        delivery_price = DELIVERY_PRICES.get(delivery_method, DELIVERY_PRICES[Order.DeliveryMethod.NP])
        dmeta_all = delivery_meta()
        meta = dmeta_all.get(delivery_method, dmeta_all['np'])
        pmeta_all = payment_meta()

        order = None
        step = self.step
        if step == 'done':
            order_id = self.request.session.get('last_order_id')
            if order_id:
                order = Order.objects.prefetch_related('items').filter(pk=order_id).first()
        if not items and step != 'done':
            step = 'checkout'

        delivery_options = []
        for value, title in Order.DeliveryMethod.choices:
            dmeta = dmeta_all.get(value, {})
            price = DELIVERY_PRICES.get(value, Decimal('0'))
            delivery_options.append(
                {
                    'value': value,
                    'title': tr(title),
                    'note': dmeta.get('note', ''),
                    'addr_label': dmeta.get('addr_label', ''),
                    'addr_ph': dmeta.get('addr_ph', ''),
                    'price': price,
                    'price_label': tr('Безкоштовно') if price == 0 else format_uah(price),
                    'free': price == 0,
                    'active': delivery_method == value,
                }
            )

        payment_value = (
            (form.data.get('payment_method') if form and form.is_bound else None)
            or (form.initial.get('payment_method') if form else None)
            or Order.PaymentMethod.CARD
        )
        payment_options = []
        for value, title in Order.PaymentMethod.choices:
            # design order: card, cod, invoice
            payment_options.append(
                {
                    'value': value,
                    'title': tr(title),
                    'note': pmeta_all.get(value, {}).get('note', ''),
                    'active': payment_value == value,
                }
            )
        payment_order = {'card': 0, 'cod': 1, 'invoice': 2}
        payment_options.sort(key=lambda x: payment_order.get(x['value'], 99))

        ctx.update(
            {
                'cart_items': items,
                'cart_subtotal': subtotal,
                'cart_subtotal_old': subtotal_old,
                'cart_savings': savings,
                'cart_qty_total': qty_total,
                'delivery_price': delivery_price,
                'delivery_method': delivery_method,
                'order_total': subtotal + delivery_price,
                'step': step if items or step == 'done' else 'checkout',
                'is_empty': not items and step != 'done',
                'order': order,
                'delivery_choices': Order.DeliveryMethod.choices,
                'payment_choices': Order.PaymentMethod.choices,
                'delivery_prices': DELIVERY_PRICES,
                'delivery_options': delivery_options,
                'payment_options': payment_options,
                'checkout_steps': build_checkout_steps(step),
                'addr_label': meta.get('addr_label') or 'Адреса',
                'addr_ph': meta.get('addr_ph') or '',
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
