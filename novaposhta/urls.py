from django.urls import path

from novaposhta.views import CitiesApiView, WarehousesApiView

app_name = 'novaposhta'

urlpatterns = [
    path('cities/', CitiesApiView.as_view(), name='cities'),
    path('warehouses/', WarehousesApiView.as_view(), name='warehouses'),
]
