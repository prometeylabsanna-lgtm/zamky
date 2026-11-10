"""Одноразовий bootstrap SQLite-демо на Vercel (migrate + seed + admin)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_FLAG = Path('/tmp/.zamky_bootstrapped_v4')


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
