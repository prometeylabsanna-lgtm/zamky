from django.urls import path

from .views import CheckoutView, OrderSuccessView, QuickOrderView, SetDistrictView

app_name = 'orders'

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order/<slug:number>/', OrderSuccessView.as_view(), name='success'),
    path('district/', SetDistrictView.as_view(), name='set_district'),
    path('orders/quick/<int:pk>/', QuickOrderView.as_view(), name='quick'),
]
