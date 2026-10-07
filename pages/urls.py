from django.urls import path

from .views import ContactSubmitView, InfoView, SetLangView

app_name = 'pages'

urlpatterns = [
    path('lang/', SetLangView.as_view(), name='set_lang'),
    path('info/', InfoView.as_view(), name='info'),
    path('info/contact/', ContactSubmitView.as_view(), name='contact'),
    path('info/<slug:page>/', InfoView.as_view(), name='info_page'),
]
