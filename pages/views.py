import uuid

from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import translate_url
from django.views import View
from django.views.generic import TemplateView

from pages.i18n_lib import tr

from . import info_content
from .forms import ContactForm
from .models import ContactRequest

INFO_PAGES = {
    'about': {'name': 'Про нас'},
    'delivery': {'name': 'Доставка і оплата'},
    'offer': {'name': 'Договір оферти'},
    'privacy': {'name': 'Політика конфіденційності'},
}

INFO_NAV = ('about', 'delivery', 'offer', 'privacy')

LANG_ALIASES = {
    'UA': 'uk',
    'RU': 'ru',
    'ua': 'uk',
    'ru': 'ru',
    'UK': 'uk',
    'uk': 'uk',
}


def _page_key(raw):
    if raw == 'contacts':
        return 'about'
    if raw in INFO_PAGES:
        return raw
    return 'about'


def _new_form(request, data=None):
    key = request.session.get('contact_idempotency') or uuid.uuid4().hex
    request.session['contact_idempotency'] = key
    if data is None:
        return ContactForm(initial={'idempotency_key': key})
    return ContactForm(data)


def _save_contact(form):
    key = form.cleaned_data['idempotency_key']
    obj, _created = ContactRequest.objects.get_or_create(
        idempotency_key=key,
        defaults={
            'name': form.cleaned_data['name'],
            'phone': form.cleaned_data['phone'],
            'email': form.cleaned_data.get('email') or '',
            'topic': form.cleaned_data['topic'],
            'message': form.cleaned_data['message'],
            'consent': True,
        },
    )
    return obj


class SetLangView(View):
    def post(self, request):
        raw = (request.POST.get('lang') or 'uk').strip()
        code = LANG_ALIASES.get(raw, LANG_ALIASES.get(raw.upper(), 'uk'))
        if code not in dict(settings.LANGUAGES):
            code = settings.LANGUAGE_CODE

        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or f'/{code}/'
        # translate_url() uses the *current* language as source — do not activate target first.
        try:
            translated = translate_url(next_url, code)
        except Exception:
            translated = None
        if not translated or translated == next_url:
            # Fallback: swap /uk|/ru prefix manually.
            from urllib.parse import urlsplit, urlunsplit
            import re

            parts = urlsplit(next_url)
            path = parts.path or '/'
            path = re.sub(r'^/(uk|ru)(?=/|$)', f'/{code}', path)
            if not path.startswith(f'/{code}'):
                path = f'/{code}{path if path.startswith("/") else "/" + path}'
            translated = urlunsplit(('', '', path, parts.query, parts.fragment))

        response = redirect(translated)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            code,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
            httponly=False,
        )
        request.session['lang'] = code
        return response


class InfoView(TemplateView):
    template_name = 'pages/info.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        raw = self.kwargs.get('page', 'about')
        page_key = _page_key(raw)
        pages = {
            key: {'name': tr(INFO_PAGES[key]['name'])}
            for key in INFO_NAV
        }
        ctx.update(
            {
                'page_key': page_key,
                'page_name': tr(INFO_PAGES[page_key]['name']),
                'info_pages': pages,
                'info_content': info_content.for_page(page_key),
                'scroll_form': raw == 'contacts',
                'form': ctx.get('form') or _new_form(self.request),
            }
        )
        return ctx


def _info_context(request, **extra):
    view = InfoView()
    view.setup(request)
    ctx = view.get_context_data()
    ctx.update(extra)
    return ctx


class ContactSubmitView(View):
    def get(self, request):
        request.session.pop('contact_idempotency', None)
        return render(
            request,
            'pages/partials/contact_idle.html',
            {'form': _new_form(request)},
        )

    def post(self, request):
        form = _new_form(request, request.POST)
        hx = request.headers.get('HX-Request') == 'true'
        if form.is_valid():
            obj = _save_contact(form)
            request.session.pop('contact_idempotency', None)
            ctx = {'done_name': obj.name, 'done_phone': obj.phone}
            if hx:
                return render(request, 'pages/partials/contact_success.html', ctx)
            return render(
                request,
                'pages/info.html',
                _info_context(request, form_done=True, **ctx),
            )
        if hx:
            return render(request, 'pages/partials/contact_idle.html', {'form': form})
        return render(request, 'pages/info.html', _info_context(request, form=form))
