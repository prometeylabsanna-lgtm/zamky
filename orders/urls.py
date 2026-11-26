from django.urls import path

from .views import CheckoutView, OrderSuccessView, QuickOrderView, SetDistrictView
from .views_payment import PaymentReturnView, PaymentStubPayView, PaymentWaitView

app_name = 'orders'

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('checkout/pay/<slug:number>/', PaymentWaitView.as_view(), name='pay_wait'),
    path(
        'checkout/pay/<slug:number>/return/',
        PaymentReturnView.as_view(),
        name='pay_return',
    ),
    path(
        'checkout/pay/<slug:number>/stub/',
        PaymentStubPayView.as_view(),
        name='pay_stub',
    ),
    path('order/<slug:number>/', OrderSuccessView.as_view(), name='success'),
    path('district/', SetDistrictView.as_view(), name='set_district'),
    path('orders/quick/<int:pk>/', QuickOrderView.as_view(), name='quick'),
]
