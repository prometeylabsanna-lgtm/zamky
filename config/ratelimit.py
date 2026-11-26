"""Обмеження частоти POST на логін і форми, та GET довідника Нової пошти."""

from __future__ import annotations

import logging
import re
import time

from django.conf import settings
from django.http import HttpResponse

from config.cache_safe import cache_get, cache_set

logger = logging.getLogger(__name__)

_LANG_RE = re.compile(r'^/(?:ua|ru|uk)(?=/|$)')
_IP_RE = re.compile(r'^[0-9a-fA-F:.]+$')

LOGIN_LIMIT = 8
LOGIN_WINDOW = 15 * 60
FORM_LIMIT = 8
FORM_WINDOW = 10 * 60
NP_LIMIT = 120
NP_WINDOW = 60

FORM_PREFIXES = (
    '/checkout',
    '/orders/quick/',
    '/info/contact',
    '/callback',
    '/photo-pick',
    '/install',
)

_MSG = 'Забагато запитів. Спробуйте пізніше.'


def client_ip(request) -> str:
    real = (request.META.get('HTTP_X_REAL_IP') or '').split(',')[0].strip()
    if real and _IP_RE.match(real) and len(real) <= 45:
        return real
    remote = (request.META.get('REMOTE_ADDR') or '').split(',')[0].strip()
    if remote and _IP_RE.match(remote) and len(remote) <= 45:
        return remote
    return '0.0.0.0'


def _strip_lang(path: str) -> str:
    raw = _LANG_RE.sub('', path or '') or '/'
    if not raw.startswith('/'):
        raw = '/' + raw
    return raw


def _is_admin_login(path: str) -> bool:
    prefix = '/' + settings.ADMIN_URL.strip('/')
    return path.rstrip('/') == f'{prefix}/login'


def _is_np_api(path: str) -> bool:
    raw = _strip_lang(path)
    return raw == '/api/np' or raw.startswith('/api/np/')


def _form_bucket(path: str) -> str | None:
    raw = _strip_lang(path)
    for prefix in FORM_PREFIXES:
        base = prefix.rstrip('/')
        if raw == base or raw == base + '/' or raw.startswith(base + '/'):
            return base
    return None


def _allowed(cache_key: str, limit: int, window_sec: int) -> bool:
    now = time.time()
    stamps = cache_get(cache_key) or []
    if not isinstance(stamps, list):
        stamps = []
    stamps = [t for t in stamps if isinstance(t, (int, float)) and now - t < window_sec]
    if len(stamps) >= limit:
        cache_set(cache_key, stamps, timeout=window_sec)
        return False
    stamps.append(now)
    if not cache_set(cache_key, stamps, timeout=window_sec):
        logger.warning('ratelimit cache unavailable')
        return True
    return True


def check_request(request) -> HttpResponse | None:
    path = request.path or '/'
    if request.method == 'GET' and _is_np_api(path):
        key = f'rl:np:{client_ip(request)}'
        if _allowed(key, NP_LIMIT, NP_WINDOW):
            return None
        return _deny()
    if request.method != 'POST':
        return None
    ip = client_ip(request)
    if _is_admin_login(path):
        key = f'rl:login:{ip}'
        if _allowed(key, LOGIN_LIMIT, LOGIN_WINDOW):
            return None
        return _deny()
    bucket = _form_bucket(path)
    if not bucket:
        return None
    key = f'rl:form:{ip}:{bucket}'
    if _allowed(key, FORM_LIMIT, FORM_WINDOW):
        return None
    return _deny()


def _deny() -> HttpResponse:
    return HttpResponse(
        _MSG,
        status=429,
        content_type='text/plain; charset=utf-8',
        headers={'Retry-After': '60'},
    )
