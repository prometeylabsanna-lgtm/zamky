import uuid

from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from .forms import ContactForm
from .models import ContactRequest

INFO_PAGES = {
    'about': {'name': 'Про нас'},
    'delivery': {'name': 'Доставка і оплата'},
    'offer': {'name': 'Договір оферти'},
    'privacy': {'name': 'Політика конфіденційності'},
}

INFO_NAV = ('about', 'delivery', 'offer', 'privacy')


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
        code = (request.POST.get('lang') or 'UA').upper()
        if code not in ('UA', 'EN', 'RU'):
            code = 'UA'
        request.session['lang'] = code
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
        response = redirect(next_url)
        if request.headers.get('HX-Request') == 'true' or request.POST.get('ajax'):
            response = render(request, 'partials/lang_label.html', {'site_lang': code})
        response.set_cookie(
            'zamky_lang',
            code,
            max_age=60 * 60 * 24 * 365,
            samesite='Lax',
            httponly=False,
        )
        return response


class InfoView(TemplateView):
    template_name = 'pages/info.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        raw = self.kwargs.get('page', 'about')
        page_key = _page_key(raw)
        ctx.update(
            {
                'page_key': page_key,
                'page_name': INFO_PAGES[page_key]['name'],
                'info_pages': {key: INFO_PAGES[key] for key in INFO_NAV},
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
