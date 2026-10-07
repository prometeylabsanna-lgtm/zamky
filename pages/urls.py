from django.urls import path

from .views import InfoView

app_name = 'pages'

urlpatterns = [
    path('info/', InfoView.as_view(), name='info'),
    path('info/<slug:page>/', InfoView.as_view(), name='info_page'),
]
