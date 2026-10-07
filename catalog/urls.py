from django.urls import path

from .views import CatalogView, HomeView, ProductDetailView

app_name = 'catalog'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('kyiv/', HomeView.as_view(), name='city'),
    path('kyiv/<slug:district_slug>/', HomeView.as_view(), name='district'),
    path('catalog/', CatalogView.as_view(), name='catalog'),
    path('catalog/<slug:slug>/', CatalogView.as_view(), name='category'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product'),
]
