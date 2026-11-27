import uuid
from decimal import Decimal

from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView

from cart.services import CartService
from catalog.models import Product
from pages.i18n_lib import tr

from .forms import CheckoutForm
from .models import Order, QuickOrder
from .services import CheckoutError, create_order_from_cart, delivery_prices
from .utils import cms_checkout, delivery_meta, format_uah, payment_meta


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

    def get(self, request, *args, **kwargs):
        if self.step == 'done':
            order_id = request.session.get('last_order_id')
            if order_id:
                order = Order.objects.filter(pk=order_id).first()
                if (
                    order
                    and order.payment_method == Order.PaymentMethod.CARD
                    and order.status == Order.Status.AWAITING_PAYMENT
                ):
                    return redirect('orders:pay_wait', number=order.number)
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['idempotency_key'] = self.request.session.get('checkout_idempotency') or uuid.uuid4().hex
        self.request.session['checkout_idempotency'] = initial['idempotency_key']
        initial.setdefault('payment_method', Order.PaymentMethod.CARD)
        initial.setdefault('delivery_method', Order.DeliveryMethod.NP)
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        key = self.request.session.get('checkout_idempotency') or uuid.uuid4().hex
        self.request.session['checkout_idempotency'] = key
        data = kwargs.get('data')
        if data is not None:
            data = data.copy()
            data['idempotency_key'] = key
            kwargs['data'] = data
        return kwargs

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
        cart_warning = self.cart.warnings_text()
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
        prices = delivery_prices()
        delivery_price = prices.get(delivery_method, prices[Order.DeliveryMethod.NP])
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

        free_label = cms_checkout('ship_free')
        delivery_options = []
        for value, title in Order.DeliveryMethod.choices:
            dmeta = dmeta_all.get(value, {})
            price = dmeta.get('price', prices.get(value, Decimal('0')))
            delivery_options.append(
                {
                    'value': value,
                    'title': dmeta.get('title') or tr(title),
                    'note': dmeta.get('note', ''),
                    'addr_label': dmeta.get('addr_label', ''),
                    'addr_ph': dmeta.get('addr_ph', ''),
                    'price': price,
                    'price_label': free_label if price == 0 else format_uah(price),
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
                    'title': pmeta_all.get(value, {}).get('title') or tr(title),
                    'note': pmeta_all.get(value, {}).get('note', ''),
                    'active': payment_value == value,
                }
            )
        payment_order = {'card': 0, 'cod': 1, 'invoice': 2}
        payment_options.sort(key=lambda x: payment_order.get(x['value'], 99))
        done_title = ''
        done_text = ''
        order_delivery_title = ''
        order_payment_title = ''
        if order is not None:
            done_title = cms_checkout('chk_done_title').replace('{number}', order.number)
            done_text = (
                cms_checkout('chk_done_text')
                .replace('{name}', order.first_name)
                .replace('{phone}', order.phone)
            )
            order_delivery_title = dmeta_all.get(order.delivery_method, {}).get('title', '')
            order_payment_title = pmeta_all.get(order.payment_method, {}).get('title', '')

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
                'done_title': done_title,
                'done_text': done_text,
                'order_delivery_title': order_delivery_title,
                'order_payment_title': order_payment_title,
                'delivery_choices': Order.DeliveryMethod.choices,
                'payment_choices': Order.PaymentMethod.choices,
                'delivery_prices': prices,
                'delivery_options': delivery_options,
                'payment_options': payment_options,
                'checkout_steps': build_checkout_steps(step),
                'addr_label': meta.get('addr_label') or 'Адреса',
                'addr_ph': meta.get('addr_ph') or '',
                'cart_warning': cart_warning,
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
        if (
            order.payment_method == Order.PaymentMethod.CARD
            and order.status == Order.Status.AWAITING_PAYMENT
        ):
            return redirect('orders:pay_wait', number=order.number)
        return redirect(f"{reverse('orders:checkout')}?step=done")

    def form_invalid(self, form):
        self.step = 'checkout'
        return super().form_invalid(form)


class OrderSuccessView(View):
    """Гостьовий thanks лише через session last_order_id (SEC-01)."""

    def get(self, request, number):
        last_id = request.session.get('last_order_id')
        if not last_id:
            raise Http404()
        get_object_or_404(Order, pk=last_id, number=number)
        return redirect(f"{reverse('orders:checkout')}?step=done")


class QuickOrderView(View):
    def post(self, request, pk):
        from django.core.exceptions import ValidationError as DjangoValidationError

        from config.validators import MSG_PHONE, clean_person_name, normalize_ua_phone

        product = get_object_or_404(Product, pk=pk, is_active=True)
        raw = (request.POST.get('phone') or '').strip()
        phone = normalize_ua_phone(raw)
        if not phone:
            context = {'error': tr(MSG_PHONE), 'product': product, 'phone_value': raw}
            if request.headers.get('HX-Request') == 'true':
                return render(request, 'orders/partials/quick_order_form.html', context)
            return HttpResponseBadRequest(context['error'])
        try:
            name = clean_person_name(request.POST.get('name') or '', required=False)[:100]
        except DjangoValidationError as exc:
            error = ' '.join(exc.messages) if getattr(exc, 'messages', None) else str(exc)
            context = {'error': error, 'product': product, 'phone_value': raw}
            if request.headers.get('HX-Request') == 'true':
                return render(request, 'orders/partials/quick_order_form.html', context)
            return HttpResponseBadRequest(context['error'])
        if product.stock <= 0:
            context = {
                'error': tr('Товару немає в наявності.'),
                'product': product,
                'phone_value': raw,
            }
            if request.headers.get('HX-Request') == 'true':
                return render(request, 'orders/partials/quick_order_form.html', context)
            return HttpResponseBadRequest(context['error'])
        try:
            qty = max(1, int(request.POST.get('quantity', 1)))
        except (TypeError, ValueError):
            qty = 1
        if qty > product.stock:
            context = {
                'error': tr('Доступно лише {n} шт.').format(n=product.stock),
                'product': product,
                'phone_value': raw,
            }
            if request.headers.get('HX-Request') == 'true':
                return render(request, 'orders/partials/quick_order_form.html', context)
            return HttpResponseBadRequest(context['error'])
        QuickOrder.objects.create(
            product=product,
            phone=phone,
            name=name,
            quantity=qty,
        )
        if request.headers.get('HX-Request') == 'true':
            return render(request, 'orders/partials/quick_order_done.html', {'product': product})
        return redirect(product.get_absolute_url())