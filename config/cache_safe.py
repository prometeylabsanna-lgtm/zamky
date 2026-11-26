"""Кеш, який не кладе вітрину, якщо таблиця/бекенд недоступні."""

from __future__ import annotations

import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


def cache_get(key, default=None):
    try:
        return cache.get(key, default)
    except Exception:
        logger.warning('cache get failed key=%s', key)
        return default


def cache_set(key, value, timeout=None) -> bool:
    try:
        cache.set(key, value, timeout)
        return True
    except Exception:
        logger.warning('cache set failed key=%s', key)
        return False


def cache_delete(key) -> None:
    try:
        cache.delete(key)
    except Exception:
        logger.warning('cache delete failed key=%s', key)


def cache_add(key, value, timeout) -> bool:
    try:
        return cache.add(key, value, timeout)
    except Exception:
        logger.warning('cache add failed key=%s', key)
        return True


def cache_incr(key, delta=1):
    try:
        return cache.incr(key, delta)
    except ValueError:
        return None
    except Exception:
        logger.warning('cache incr failed key=%s', key)
        return None
