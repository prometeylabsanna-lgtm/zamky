from django.core.management.base import BaseCommand

from orders.payments import release_expired_payment_holds


class Command(BaseCommand):
    help = 'Повертає залишок для прострочених карткових резервів.'

    def handle(self, *args, **options):
        released = release_expired_payment_holds()
        self.stdout.write(f'released {released}')
