"""Публічні маркетингові URL: /feeds/<slug>.xml, /robots.txt і /llms.txt."""

from __future__ import annotations

import secrets

from django.http import Http404, HttpResponse, HttpResponseNotModified
from django.shortcuts import get_object_or_404
from django.urls import NoReverseMatch, reverse
from django.utils.http import http_date
from django.utils.translation import override
from django.views.decorators.http import require_GET

from marketing.feeds import get_feed_payload, resolve_base_url
from marketing.llms import build_llms_txt
from marketing.models import ProductFeed, SeoSettings

_ROBOTS_LANGS = ("ua", "ru")
_ROBOTS_NAMED = (
    "cart:drawer",
    "orders:checkout",
    "catalog:api_picker",
    "pages:callback",
    "pages:photo_pick",
    "pages:install",
)


@require_GET
def feed_view(request, slug: str):
    feed = get_object_or_404(ProductFeed, slug=slug, is_enabled=True)
    if feed.access_token:
        given = request.GET.get("token", "")
        if not secrets.compare_digest(given.encode(), feed.access_token.encode()):
            raise Http404
    payload = get_feed_payload(feed, resolve_base_url(request))
    if request.headers.get("If-None-Match") == payload.etag:
        resp = HttpResponseNotModified()
    else:
        resp = HttpResponse(payload.body, content_type="application/xml; charset=utf-8")
    resp["ETag"] = payload.etag
    resp["Last-Modified"] = http_date(payload.last_modified.timestamp())
    resp["X-Robots-Tag"] = "noindex"
    resp["Cache-Control"] = "public, max-age=900"
    return resp


def _sitemap_url(base: str) -> str:
    for name in ("sitemap", "django.contrib.sitemaps.views.sitemap", "django.contrib.sitemaps.views.index"):
        try:
            return f"{base}{reverse(name)}"
        except NoReverseMatch:
            continue
    return ""


def _prefix_disallow(path: str, depth: int = 2) -> str:
    parts = [p for p in path.split("/") if p]
    if len(parts) < depth:
        return path if path.endswith("/") else path + "/"
    return "/" + "/".join(parts[:depth]) + "/"


def _robots_disallow() -> list[str]:
    lines = [
        "Disallow: /feeds/",
        "Disallow: /healthz/",
        "Disallow: /lang/",
    ]
    seen = set(lines)
    for lang in _ROBOTS_LANGS:
        with override(lang):
            for name in _ROBOTS_NAMED:
                try:
                    path = reverse(name)
                except NoReverseMatch:
                    continue
                rule = f"Disallow: {_prefix_disallow(path)}"
                if rule not in seen:
                    seen.add(rule)
                    lines.append(rule)
            rule = f"Disallow: /{lang}/order/"
            if rule not in seen:
                seen.add(rule)
                lines.append(rule)
    return lines


@require_GET
def robots_txt(request):
    seo = SeoSettings.load()
    base = (seo.primary_domain or "").rstrip("/") or f"{request.scheme}://{request.get_host()}"
    # Глобальний noindex працює через <meta name="robots"> на кожній сторінці,
    # а не через Disallow: / (інакше бот не побачить noindex і URL лишаться в індексі).
    lines = ["User-agent: *", *_robots_disallow()]
    extra = [ln.strip() for ln in (seo.robots_extra or "").splitlines() if ln.strip()]
    if extra:
        lines.append("")
        lines += extra
    sitemap = _sitemap_url(base)
    if sitemap:
        lines += ["", f"Sitemap: {sitemap}"]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


@require_GET
def llms_txt(request):
    body = build_llms_txt(request)
    return HttpResponse(body, content_type="text/plain; charset=utf-8")
