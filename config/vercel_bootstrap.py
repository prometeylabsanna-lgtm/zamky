"""Одноразовий bootstrap SQLite-демо на Vercel (migrate + seed + admin)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_FLAG = Path('/tmp/.zamky_bootstrapped_v4')

# Пароль суперюзера — лише з env Vercel (без дефолту в коді).
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_ENV = 'DJANGO_SUPERUSER_PASSWORD'


def _ensure_admin_from_env(user_model) -> None:
    password = os.environ.get(ADMIN_PASSWORD_ENV, '')
    if not password.strip():
        logger.warning(
            'Vercel bootstrap: %s не задано — суперюзера %s не створюю',
            ADMIN_PASSWORD_ENV,
            ADMIN_USERNAME,
        )
        return
    if user_model.objects.filter(username=ADMIN_USERNAME).exists():
        return
    logger.info('Vercel bootstrap: create superuser %s', ADMIN_USERNAME)
    user_model.objects.create_superuser(
        username=ADMIN_USERNAME,
        email='admin@example.com',
        password=password,
    )


def bootstrap_if_needed() -> None:
    if os.environ.get('VERCEL') != '1':
        return
    if _FLAG.exists():
        return

    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    logger.info('Vercel bootstrap: migrate')
    call_command('migrate', interactive=False, run_syncdb=True)

    # Завжди повний seed: товари + ProductAttribute (brand/country/color/mech),
    # інакше на «теплій» SQLite у /tmp лишаються товари без фільтрів (counts=0).
    logger.info('Vercel bootstrap: seed_demo')
    call_command('seed_demo')

    logger.info('Vercel bootstrap: seed_cms_content')
    call_command('seed_cms_content')

    _ensure_admin_from_env(get_user_model())

    _FLAG.write_text('ok', encoding='utf-8')
    logger.info('Vercel bootstrap: done')
