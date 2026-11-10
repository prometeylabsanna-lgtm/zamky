"""Окрема сторінка «Недавні дії» + URL у admin.site."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.shortcuts import render
from django.urls import path

RECENT_ACTIONS_LIMIT = 100

_urls_patched = False


def recent_actions_view(request):
    qs = LogEntry.objects.select_related('content_type', 'user').order_by('-action_time')
    if not request.user.is_superuser:
        qs = qs.filter(user=request.user)

    context = {
        **admin.site.each_context(request),
        'title': 'Недавні дії',
        'admin_log': list(qs[:RECENT_ACTIONS_LIMIT]),
        'opts': LogEntry._meta,
        'has_view_permission': True,
        'has_change_permission': False,
    }
    return render(request, 'admin/recent_actions.html', context)


def patch_admin_urls() -> None:
    global _urls_patched
    if _urls_patched:
        return
    _urls_patched = True
    original_get_urls = admin.site.get_urls

    def get_urls():
        custom = [
            path(
                'recent-actions/',
                admin.site.admin_view(recent_actions_view),
                name='recent_actions',
            ),
        ]
        return custom + original_get_urls()

    admin.site.get_urls = get_urls
