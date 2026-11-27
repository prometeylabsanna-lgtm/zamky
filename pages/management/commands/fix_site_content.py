"""Ідемпотентні правки контенту: лише хибні або порожні значення.

Не перетирає те, що власник уже змінив. --dry-run нічого не пише.
"""

from django.core.management.base import BaseCommand

from pages.models_cms import SiteSettings
from pages.phone import DEFAULT_EMAIL, DEFAULT_HOURS

OLD_EMAIL = "info@centrzamkiv.ua"
HOURS_UA = DEFAULT_HOURS
HOURS_RU = "Ежедневно 8:00-21:00"
ADDRESS_UA = "м. Київ"
ADDRESS_RU = "г. Киев"


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


def step_hours_address(stdout, dry_run: bool) -> str:
    obj = SiteSettings.objects.filter(pk=1).first()
    if obj is None:
        line = "графік/адреса: немає SiteSettings — пропуск"
        stdout.write(line)
        return line
    notes: list[str] = []
    updates: dict[str, str] = {}
    hours = (obj.work_hours or "").strip()
    hours_ru = (obj.work_hours_ru or "").strip()
    if not hours_ru and hours == HOURS_UA:
        updates["work_hours_ru"] = HOURS_RU
        notes.append(f"графік RU: порожньо → {HOURS_RU}")
    elif not hours_ru:
        notes.append(f"графік RU: не чіпаю, work_hours = {hours or 'порожньо'}")
    else:
        notes.append("графік RU: уже заповнено")
    address = (obj.address or "").strip()
    address_ru = (obj.address_ru or "").strip()
    if not address_ru and address == ADDRESS_UA:
        updates["address_ru"] = ADDRESS_RU
        notes.append(f"адреса RU: порожньо → {ADDRESS_RU}")
    elif not address_ru:
        notes.append(f"адреса RU: не чіпаю, address = {address or 'порожньо'}")
    else:
        notes.append("адреса RU: уже заповнено")
    if updates and not dry_run:
        for field, value in updates.items():
            setattr(obj, field, value)
        obj.save(update_fields=list(updates))
    line = "; ".join(notes)
    stdout.write(line)
    return line


SOCIAL_DEFAULTS = (
    ("instagram_url", "https://www.instagram.com/"),
    ("telegram_url", "https://t.me/"),
    ("viber_url", "https://www.viber.com/"),
    ("facebook_url", "https://www.facebook.com/"),
)


def step_social(stdout, dry_run: bool) -> str:
    obj = SiteSettings.objects.filter(pk=1).first()
    if obj is None:
        line = "соцмережі: немає SiteSettings — пропуск"
        stdout.write(line)
        return line
    updates: dict[str, str] = {}
    notes: list[str] = []
    for field, url in SOCIAL_DEFAULTS:
        current = (getattr(obj, field) or "").strip()
        if current:
            notes.append(f"{field}: уже є")
            continue
        updates[field] = url
        notes.append(f"{field}: порожньо → {url}")
    if updates and not dry_run:
        for field, value in updates.items():
            setattr(obj, field, value)
        obj.save(update_fields=list(updates))
    line = "; ".join(notes)
    stdout.write(line)
    return line


STEPS = [step_email, step_hours_address, step_social]


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
