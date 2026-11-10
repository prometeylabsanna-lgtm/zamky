"""Middleware проєкту Замки."""

from django.utils import translation


class AdminUkrainianLocaleMiddleware:
    """У /admin/ завжди українська (uk), вітрина лишає ua/ru."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin'):
            translation.activate('uk')
            request.LANGUAGE_CODE = 'uk'
        return self.get_response(request)
