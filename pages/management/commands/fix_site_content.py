"""Ідемпотентні правки контенту: лише хибні або порожні значення.

Не перетирає те, що власник уже змінив. --dry-run нічого не пише.
"""

from django.core.management.base import BaseCommand

from pages.models_cms import SiteSettings
from pages.phone import DEFAULT_EMAIL

OLD_EMAIL = "info@centrzamkiv.ua"


def step_email(stdout, dry_run: bool) -> str:
    obj = SiteSettings.objects.filter(pk=1).first()
    if obj is None:
        line = "email: немає SiteSettings — пропуск"
        stdout.write(line)
        return line
    current = (obj.email or "").strip()
    if current != OLD_EMAIL:
        line = f"email: не чіпаю ({current or 'порожньо'})"
        stdout.write(line)
        return line
    if not dry_run:
        obj.email = DEFAULT_EMAIL
        obj.save(update_fields=["email"])
    line = f"email: {OLD_EMAIL} → {DEFAULT_EMAIL}"
    stdout.write(line)
    return line


STEPS = [step_email]


class Command(BaseCommand):
    help = "Виправити хибні/порожні контакти й тексти, не затираючи правки власника."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише надрукувати зміни, без запису.",
        )

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        if dry_run:
            self.stdout.write("dry-run: запису не буде")
        for step in STEPS:
            step(self.stdout, dry_run)
        self.stdout.write(self.style.SUCCESS(f"Кроків: {len(STEPS)}"))
