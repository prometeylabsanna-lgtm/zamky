from django.urls import path

from .views import ContactSubmitView, InfoView
from .views_extra import (
    BlogDetailView,
    BlogListView,
    CallbackSubmitView,
    InstallSubmitView,
    PhotoPickSubmitView,
)

app_name = 'pages'

urlpatterns = [
    path('info/', InfoView.as_view(), name='info'),
    path('info/contact/', ContactSubmitView.as_view(), name='contact'),
    path('info/blog/', BlogListView.as_view(), name='blog_list'),
    path('info/blog/<slug:slug>/', BlogDetailView.as_view(), name='blog_detail'),
    path('info/<slug:page>/', InfoView.as_view(), name='info_page'),
    path('callback/', CallbackSubmitView.as_view(), name='callback'),
    path('photo-pick/', PhotoPickSubmitView.as_view(), name='photo_pick'),
    path('install/', InstallSubmitView.as_view(), name='install'),
]
