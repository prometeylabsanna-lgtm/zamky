"""Одноразовий bootstrap SQLite-демо на Vercel (migrate + seed + admin)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_FLAG = Path('/tmp/.zamky_bootstrapped')


def bootstrap_if_needed() -> None:
    if os.environ.get('VERCEL') != '1':
        return
    if _FLAG.exists():
        return

    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    from catalog.models import Product

    logger.info('Vercel bootstrap: migrate')
    call_command('migrate', interactive=False, run_syncdb=True)

    if not Product.objects.exists():
        logger.info('Vercel bootstrap: seed_demo')
        call_command('seed_demo')

    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        logger.info('Vercel bootstrap: create superuser admin')
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin',
        )

    _FLAG.write_text('ok', encoding='utf-8')
    logger.info('Vercel bootstrap: done')
