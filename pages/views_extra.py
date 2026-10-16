import uuid

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import DetailView, ListView

from pages.i18n_lib import tr

from .forms_extra import CallbackForm, InstallForm, PhotoPickForm
from .models_extra import (
    BlogPost,
    CallbackRequest,
    InstallRequest,
    PhotoPickImage,
    PhotoPickRequest,
)

MAX_PICKER_PHOTOS = 5
MAX_PICKER_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = ('image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif')


def _session_key(prefix):
    return f'{prefix}_idempotency'


def _form_with_key(request, form_cls, prefix, data=None):
    sk = _session_key(prefix)
    key = request.session.get(sk) or uuid.uuid4().hex
    request.session[sk] = key
    if data is None:
        return form_cls(initial={'idempotency_key': key})
    if 'idempotency_key' not in data:
        data = data.copy()
        data['idempotency_key'] = key
    return form_cls(data)


def _wants_json(request):
    if request.GET.get('format') == 'json':
        return True
    accept = request.headers.get('Accept', '')
    return 'application/json' in accept and 'text/html' not in accept


def _respond(request, *, ok, hx_template=None, hx_ctx=None, json_extra=None, html_template=None, html_ctx=None):
    if _wants_json(request):
        payload = {'ok': ok}
        if json_extra:
            payload.update(json_extra)
        if not ok and hx_ctx and hx_ctx.get('form'):
            payload['errors'] = hx_ctx['form'].errors.get_json_data()
        status = 200 if ok else 400
        return JsonResponse(payload, status=status)
    if request.headers.get('HX-Request') == 'true' and hx_template:
        return render(request, hx_template, hx_ctx or {})
    if html_template:
        return render(request, html_template, html_ctx or {})
    return JsonResponse({'ok': ok})


class CallbackSubmitView(View):
    def post(self, request):
        form = _form_with_key(request, CallbackForm, 'callback', request.POST)
        if form.is_valid():
            key = form.cleaned_data['idempotency_key']
            obj, _ = CallbackRequest.objects.get_or_create(
                idempotency_key=key,
                defaults={
                    'name': form.cleaned_data.get('name') or '',
                    'phone': form.cleaned_data['phone'],
                },
            )
            request.session.pop(_session_key('callback'), None)
            ctx = {
                'title': tr('Дякуємо!'),
                'message': tr(
                    'Менеджер передзвонить вам на номер {phone} протягом 15 хвилин.'
                ).format(phone=obj.phone),
            }
            return _respond(
                request,
                ok=True,
                hx_template='pages/partials/form_success.html',
                hx_ctx=ctx,
                json_extra={'phone': obj.phone},
            )
        return _respond(
            request,
            ok=False,
            hx_template='pages/partials/form_idle.html',
            hx_ctx={'form': form, 'form_id': 'callback-form'},
        )


class PhotoPickSubmitView(View):
    def post(self, request):
        form = _form_with_key(request, PhotoPickForm, 'photo_pick', request.POST)
        files = request.FILES.getlist('photos') or request.FILES.getlist('images')
        file_errors = self._validate_files(files)
        if file_errors:
            for msg in file_errors:
                form.add_error(None, msg)

        if form.is_valid() and not file_errors:
            key = form.cleaned_data['idempotency_key']
            obj, created = PhotoPickRequest.objects.get_or_create(
                idempotency_key=key,
                defaults={
                    'phone': form.cleaned_data['phone'],
                    'channel': form.cleaned_data['channel'],
                    'note': form.cleaned_data.get('note') or '',
                },
            )
            if created and files:
                for fh in files[:MAX_PICKER_PHOTOS]:
                    PhotoPickImage.objects.create(request=obj, image=fh)
            request.session.pop(_session_key('photo_pick'), None)
            channel_label = dict(PhotoPickRequest.Channel.choices).get(
                obj.channel, obj.channel
            )
            ctx = {
                'title': tr('Фото надіслано!'),
                'message': tr(
                    'Майстер перегляне фото і надішле варіанти ({channel}) протягом 15 хвилин.'
                ).format(channel=tr(channel_label)),
            }
            return _respond(
                request,
                ok=True,
                hx_template='pages/partials/form_success.html',
                hx_ctx=ctx,
                json_extra={'phone': obj.phone, 'images': obj.images.count()},
            )
        return _respond(
            request,
            ok=False,
            hx_template='pages/partials/form_idle.html',
            hx_ctx={'form': form, 'form_id': 'photo-pick-form'},
        )

    def _validate_files(self, files):
        errors = []
        if not files:
            errors.append(tr('Додайте хоча б одне фото'))
            return errors
        if len(files) > MAX_PICKER_PHOTOS:
            errors.append(
                tr('Максимум {n} зображень').format(n=MAX_PICKER_PHOTOS)
            )
        for fh in files[:MAX_PICKER_PHOTOS]:
            ctype = (getattr(fh, 'content_type', '') or '').split(';')[0].lower()
            if ctype and ctype not in ALLOWED_IMAGE_TYPES:
                errors.append(tr('Дозволені лише зображення JPEG, PNG або WebP'))
                break
            if fh.size > MAX_PICKER_BYTES:
                errors.append(tr('Кожне фото — не більше 5 МБ'))
                break
        return errors


class InstallSubmitView(View):
    def post(self, request):
        form = _form_with_key(request, InstallForm, 'install', request.POST)
        if form.is_valid():
            key = form.cleaned_data['idempotency_key']
            obj, _ = InstallRequest.objects.get_or_create(
                idempotency_key=key,
                defaults={
                    'name': form.cleaned_data['name'],
                    'phone': form.cleaned_data['phone'],
                    'address': form.cleaned_data.get('address') or '',
                    'comment': form.cleaned_data.get('comment') or '',
                },
            )
            request.session.pop(_session_key('install'), None)
            ctx = {
                'title': tr('Заявку прийнято!'),
                'message': tr(
                    'Менеджер звʼяжеться з вами за номером {phone}, щоб узгодити час виїзду.'
                ).format(phone=obj.phone),
            }
            return _respond(
                request,
                ok=True,
                hx_template='pages/partials/form_success.html',
                hx_ctx=ctx,
                json_extra={'phone': obj.phone},
            )
        return _respond(
            request,
            ok=False,
            hx_template='pages/partials/install_form_fields.html',
            hx_ctx={'form': form},
        )


class BlogListView(ListView):
    model = BlogPost
    template_name = 'pages/blog_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True).order_by('sort_order', '-created_at')


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'pages/blog_detail.html'
    context_object_name = 'post'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['more_posts'] = (
            BlogPost.objects.filter(is_published=True)
            .exclude(pk=self.object.pk)
            .order_by('sort_order', '-created_at')[:4]
        )
        return ctx
