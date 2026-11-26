"""Відгуки на сторінці товару: форма, відправка, антиспам."""

from django import forms
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from pages.i18n_lib import tr, tr_lazy

from .models import Product, Review

RATE_LIMIT = 3  # відгуків з однієї IP
RATE_WINDOW = 60 * 60  # за годину
INITIAL_VISIBLE = 5


class ReviewForm(forms.Form):
    author_name = forms.CharField(
        label=tr_lazy('Імʼя'),
        max_length=120,
        error_messages={'required': tr_lazy('Вкажіть імʼя')},
    )
    rating = forms.TypedChoiceField(
        label=tr_lazy('Оцінка'),
        coerce=int,
        choices=[(i, str(i)) for i in range(1, 6)],
        error_messages={
            'required': tr_lazy('Поставте оцінку'),
            'invalid_choice': tr_lazy('Поставте оцінку'),
        },
    )
    text = forms.CharField(
        label=tr_lazy('Відгук'),
        min_length=10,
        max_length=3000,
        error_messages={
            'required': tr_lazy('Напишіть кілька слів про товар'),
            'min_length': tr_lazy('Напишіть кілька слів про товар'),
        },
    )
    # honeypot: людина поле не бачить, бот заповнює
    website = forms.CharField(required=False)

    def clean_author_name(self):
        return ' '.join(self.cleaned_data['author_name'].split())

    def clean_text(self):
        return self.cleaned_data['text'].strip()


def _client_ip(request):
    # останній елемент додає наш nginx — його не підробити з браузера
    fwd = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[-1].strip()
    return fwd or request.META.get('REMOTE_ADDR') or 'unknown'


def _rate_limited(request):
    key = f'review-rl:{_client_ip(request)}'
    if cache.add(key, 1, RATE_WINDOW):
        return False
    try:
        n = cache.incr(key)
    except ValueError:
        cache.set(key, 1, RATE_WINDOW)
        return False
    return n > RATE_LIMIT


class ReviewSubmitView(View):
    http_method_names = ['post']

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        form = ReviewForm(request.POST)
        is_htmx = request.headers.get('HX-Request') == 'true'
        if form.is_valid():
            # бот заповнив приховане поле — мовчки «приймаємо», нічого не зберігаємо
            if not form.cleaned_data.get('website'):
                if _rate_limited(request):
                    form.add_error(None, tr('Забагато відгуків поспіль. Спробуйте пізніше.'))
                else:
                    Review.objects.create(
                        product=product,
                        author_name=form.cleaned_data['author_name'],
                        rating=form.cleaned_data['rating'],
                        text=form.cleaned_data['text'],
                        is_published=False,
                    )
            if not form.errors:
                if is_htmx:
                    return render(request, 'catalog/partials/review_thanks.html')
                return redirect(f'{product.get_absolute_url()}?review=sent#reviews')
        if is_htmx:
            return render(
                request,
                'catalog/partials/review_form.html',
                {'product': product, 'review_form': form},
                status=200,
            )
        return redirect(f'{product.get_absolute_url()}#reviews')
