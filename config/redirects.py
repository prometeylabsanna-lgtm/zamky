"""Безпечні URL для redirect / HX-Redirect (open-redirect guard)."""

from __future__ import annotations

from django.utils.http import url_has_allowed_host_and_scheme


def safe_next_url(request, candidate: str | None, *, fallback: str = '/') -> str:
    """Повертає candidate лише якщо це відносний шлях або той самий host."""
    url = (candidate or '').strip()
    if not url:
        return fallback
    if url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return url
    return fallback
