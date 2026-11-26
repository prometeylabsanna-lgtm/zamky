"""На локальному SQLite підтягує міграції при runserver."""

from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)

_RUNSERVER = frozenset({'runserver', 'runserver_plus'})


def _is_runserver() -> bool:
    names = set(sys.argv)
    names.update(os.path.basename(arg) for arg in sys.argv[:3])
    if not names.intersection(_RUNSERVER):
        return False
    if os.environ.get('RUN_MAIN') == 'true':
        return True
    return '--noreload' in sys.argv


def autmigrate_sqlite() -> None:
    from django.conf import settings

    engine = (settings.DATABASES.get('default') or {}).get('ENGINE') or ''
    if 'sqlite3' not in engine:
        return
    if not _is_runserver():
        return
    from django.core.management import call_command

    try:
        call_command('migrate', interactive=False, verbosity=1)
    except Exception:
        logger.exception('Не вдалося застосувати міграції локальної SQLite')
        return
    from catalog.db_compat import reset_schema_cache

    reset_schema_cache()
