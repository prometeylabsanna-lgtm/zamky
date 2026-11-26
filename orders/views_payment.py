from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from pages.i18n_lib import tr

from .models import Order
from .payments import PaymentError, mark_order_paid, online_payment_enabled, verify_webhook
from .views import build_checkout_steps


def _session_order(request, number):
    last_id = request.session.get('last_order_id')
    if not last_id:
        raise Http404()
    return get_object_or_404(Order, pk=last_id, number=number)


class PaymentWaitView(View):
    template_name = 'orders/payment_wait.html'

    def get(self, request, number):
        order = _session_order(request, number)
        if order.status == Order.Status.PAID:
            return redirect(f"{reverse('orders:checkout')}?step=done")
        if order.status == Order.Status.NEW and order.payment_method != Order.PaymentMethod.CARD:
            return redirect(f"{reverse('orders:checkout')}?step=done")
        stub_on = bool(getattr(settings, 'PAYMENT_STUB_ENABLED', False))
        cancelled = order.status == Order.Status.CANCELLED
        ctx = {
            'order': order,
            'cancelled': cancelled,
            'awaiting': order.status == Order.Status.AWAITING_PAYMENT,
            'online_enabled': online_payment_enabled(),
            'stub_enabled': stub_on and order.status == Order.Status.AWAITING_PAYMENT,
            'checkout_steps': build_checkout_steps('checkout'),
            'wait_title': tr('Очікуємо оплату') if not cancelled else tr('Оплату скасовано'),
        }
        return render(request, self.template_name, ctx)


class PaymentReturnView(PaymentWaitView):
    """Повернення з банку не ставить paid."""


class PaymentStubPayView(View):
    def post(self, request, number):
        if not getattr(settings, 'PAYMENT_STUB_ENABLED', False):
            raise Http404()
        order = _session_order(request, number)
        try:
            mark_order_paid(number=order.number, payment_ref=order.payment_ref)
        except PaymentError as exc:
            raise Http404() from exc
        return redirect('orders:pay_wait', number=order.number)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(View):
    def post(self, request):
        try:
            payload = verify_webhook(request)
        except PaymentError:
            return HttpResponseForbidden('invalid signature')
        number = str(payload.get('number') or '').strip()
        ref = str(payload.get('payment_ref') or '').strip()
        status = str(payload.get('status') or '').strip().lower()
        if not number or status != 'paid':
            return HttpResponse('ignored', status=200)
        try:
            mark_order_paid(number=number, payment_ref=ref)
        except PaymentError as exc:
            if str(exc) == 'not found':
                return JsonResponse({'ok': False}, status=404)
            return HttpResponseForbidden(str(exc))
        return JsonResponse({'ok': True})
