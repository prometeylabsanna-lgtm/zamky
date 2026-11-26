from django.core.management.base import BaseCommand, CommandError

from novaposhta.models import NPSyncRun
from novaposhta.sync import sync_warehouses


class Command(BaseCommand):
    help = 'Завантажує довідник відділень Нової пошти. Можна без API-ключа.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=500)
        parser.add_argument('--max-pages', type=int, default=400)

    def handle(self, *args, **options):
        run = sync_warehouses(limit=options['limit'], max_pages=options['max_pages'])
        if run.status == NPSyncRun.Status.RUNNING and run.finished_at is None:
            self.stdout.write('Синхронізація вже виконується. Новий запуск пропущено.')
            return
        if run.status != NPSyncRun.Status.SUCCESS:
            raise CommandError(run.message or 'Синхронізація Нової пошти не вдалася.')
        self.stdout.write(
            'Синхронізацію завершено: '
            f'сторінок {run.pages}, отримано {run.received}, '
            f'створено {run.created}, оновлено {run.updated}, '
            f'деактивовано {run.deactivated}.'
        )
