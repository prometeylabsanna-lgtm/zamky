"""Middleware проєкту Замки."""

from django.conf import settings
from django.utils import translation

from config.ratelimit import check_request


class RateLimitMiddleware:
    """Ліміт POST на логін адмінки та публічні форми."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        blocked = check_request(request)
        if blocked is not None:
            return blocked
        return self.get_response(request)


class AdminUkrainianLocaleMiddleware:
    """В адмінці завжди українська (uk), вітрина лишає ua/ru."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        prefix = '/' + settings.ADMIN_URL.strip('/')
        path = request.path or ''
        is_admin = path == prefix or path.startswith(prefix + '/')
        parts = [part for part in path.split('/') if part]
        is_admin_alias = (
            len(parts) >= 2 and parts[0] in {'ua', 'ru', 'uk'} and parts[1] == 'admin'
        )
        if is_admin:
            translation.activate('uk')
            request.LANGUAGE_CODE = 'uk'
        response = self.get_response(request)
        if is_admin or is_admin_alias:
            response['X-Robots-Tag'] = 'noindex, nofollow'
        return response
