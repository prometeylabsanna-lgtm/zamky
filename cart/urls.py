from django.urls import path

from .views import (
    CartAddView,
    CartBadgeView,
    CartDrawerView,
    CartUpdateView,
    WishlistPageView,
    WishlistToggleView,
)

app_name = 'cart'

urlpatterns = [
    path('drawer/', CartDrawerView.as_view(), name='drawer'),
    path('badge/', CartBadgeView.as_view(), name='badge'),
    path('add/<int:pk>/', CartAddView.as_view(), name='add'),
    path('update/<int:pk>/', CartUpdateView.as_view(), name='update'),
    path('wishlist/', WishlistPageView.as_view(), name='wishlist_page'),
    path('wishlist/<int:pk>/', WishlistToggleView.as_view(), name='wishlist'),
]
