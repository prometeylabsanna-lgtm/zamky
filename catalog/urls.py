from django.urls import path

from .picker_api import PickerApiView
from .search_api import SearchSuggestApiView
from .views import CatalogView, HomeView, ProductDetailView

app_name = 'catalog'

urlpatterns = [
    path('api/picker/', PickerApiView.as_view(), name='api_picker'),
    path('api/search/', SearchSuggestApiView.as_view(), name='api_search'),
    path('', HomeView.as_view(), name='home'),
    path('kyiv/', HomeView.as_view(), name='city'),
    path('kyiv/<slug:district_slug>/', HomeView.as_view(), name='district'),
    path('catalog/', CatalogView.as_view(), name='catalog'),
    path('catalog/<slug:slug>/', CatalogView.as_view(), name='category'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product'),
]
