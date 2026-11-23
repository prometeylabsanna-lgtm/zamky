"""Middleware проєкту Замки."""

from django.conf import settings
from django.utils import translation


class AdminUkrainianLocaleMiddleware:
    """В адмінці завжди українська (uk), вітрина лишає ua/ru."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        prefix = '/' + settings.ADMIN_URL.strip('/')
        if request.path == prefix or request.path.startswith(prefix + '/'):
            translation.activate('uk')
            request.LANGUAGE_CODE = 'uk'
        return self.get_response(request)
