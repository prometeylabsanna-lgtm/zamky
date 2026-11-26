from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import redirect
from django.urls import include, path
from django.utils.translation import get_language
from django.views import View

from pages.views import SetLangView


def healthz(_request):
    return HttpResponse('ok')


def root_redirect(request):
    lang = get_language() or settings.LANGUAGE_CODE
    if lang not in dict(settings.LANGUAGES):
        lang = settings.LANGUAGE_CODE
    return redirect(f'/{lang}/')


class LegacyUkRedirectView(View):
    """Старий префікс /uk/ → /ua/."""

    def get(self, request, rest=''):
        target = '/ua/'
        if rest:
            target = f'/ua/{rest}'
        if request.META.get('QUERY_STRING'):
            target = f'{target}?{request.META["QUERY_STRING"]}'
        return HttpResponsePermanentRedirect(target)

    post = get


class LocalizedAdminRedirectView(View):
    """/ua/admin/ і /ru/admin/ → справжня адмінка без мовного префікса."""

    def get(self, request, rest=''):
        prefix = settings.ADMIN_URL.strip('/')
        target = f'/{prefix}/'
        if rest:
            target = f'/{prefix}/{rest}'
        qs = request.META.get('QUERY_STRING')
        if qs:
            target = f'{target}?{qs}'
        return redirect(target)

    post = get


urlpatterns = [
    path('healthz/', healthz),
    path(settings.ADMIN_URL, admin.site.urls),
    path('lang/', SetLangView.as_view(), name='set_lang'),
    path('uk/', LegacyUkRedirectView.as_view()),
    path('uk/<path:rest>', LegacyUkRedirectView.as_view()),
    # Маркетинг: фіди та robots.txt — поза i18n_patterns (стабільні URL).
    path('', include('marketing.urls')),
    path('', root_redirect),
]

urlpatterns += i18n_patterns(
    path('admin/', LocalizedAdminRedirectView.as_view()),
    path('admin/<path:rest>', LocalizedAdminRedirectView.as_view()),
    path('', include('catalog.urls')),
    path('cart/', include('cart.urls')),
    path('', include('orders.urls')),
    path('', include('pages.urls')),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
