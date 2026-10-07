from django.urls import path

from .views import ContactSubmitView, InfoView

app_name = 'pages'

urlpatterns = [
    path('info/', InfoView.as_view(), name='info'),
    path('info/contact/', ContactSubmitView.as_view(), name='contact'),
    path('info/<slug:page>/', InfoView.as_view(), name='info_page'),
]
