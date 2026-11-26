"""Клієнт довідника відділень Нової пошти. Тіло запиту з ключем не логується."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from django.conf import settings

DEFAULT_API_URL = 'https://api.novaposhta.ua/v2.0/json/'
_ATTEMPTS = 3
_TIMEOUT = 30


class NPApiError(Exception):
    """Помилка API або мережі без секретів у тексті."""


def _redact(text: str) -> str:
    raw = text or ''
    key = getattr(settings, 'NOVA_POSHTA_API_KEY', '') or ''
    if key and key in raw:
        raw = raw.replace(key, '')
    return raw.strip()[:1000]


class NovaPoshtaClient:
    def __init__(self, api_key=None, url=None, timeout=_TIMEOUT):
        self._api_key = api_key
        self._url = url
        self.timeout = timeout

    def _credentials(self):
        key = self._api_key
        if key is None:
            key = getattr(settings, 'NOVA_POSHTA_API_KEY', '') or ''
        url = self._url or getattr(settings, 'NOVA_POSHTA_API_URL', '') or DEFAULT_API_URL
        return key, url

    def get_warehouses(self, page, limit):
        key, url = self._credentials()
        body = {
            'apiKey': key or '',
            'modelName': 'AddressGeneral',
            'calledMethod': 'getWarehouses',
            'methodProperties': {
                'Page': str(page),
                'Limit': str(limit),
            },
        }
        return self._post(url, body)

    def _post(self, url, body):
        data = json.dumps(body).encode('utf-8')
        last_error = None
        for attempt in range(_ATTEMPTS):
            request = urllib.request.Request(
                url,
                data=data,
                headers={
                    'Content-Type': 'application/json; charset=utf-8',
                    'Accept': 'application/json',
                    'User-Agent': 'Zamky-NP-Sync',
                },
                method='POST',
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    status = getattr(response, 'status', 200) or 200
                    raw = response.read()
                if status >= 500:
                    last_error = NPApiError(f'Тимчасова помилка API ({status})')
                else:
                    return self._parse(raw)
            except NPApiError:
                raise
            except urllib.error.HTTPError as exc:
                if 500 <= int(exc.code) <= 599:
                    last_error = NPApiError(f'Тимчасова помилка API ({exc.code})')
                else:
                    raise NPApiError(f'API Нової пошти відхилив запит ({exc.code})') from None
            except (urllib.error.URLError, TimeoutError, OSError):
                last_error = NPApiError('Немає зʼєднання з API Нової пошти')
            if attempt + 1 < _ATTEMPTS:
                time.sleep(0.4 * (2 ** attempt))
        raise last_error or NPApiError('Не вдалося отримати відповідь API Нової пошти')

    def _parse(self, raw: bytes):
        try:
            payload = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NPApiError('Некоректна відповідь API Нової пошти') from exc
        if not isinstance(payload, dict):
            raise NPApiError('Некоректна відповідь API Нової пошти')
        if payload.get('success') not in (True, 'true', 'True', 1):
            errors = payload.get('errors') or []
            if isinstance(errors, list):
                text = '; '.join(str(item) for item in errors if item)
            else:
                text = str(errors)
            raise NPApiError(_redact(text) or 'API Нової пошти повернув помилку')
        return payload
