"""Ідемпотентні правки контенту: лише хибні або порожні значення.

Не перетирає те, що власник уже змінив. --dry-run нічого не пише.
"""

from django.core.management.base import BaseCommand

from pages.models_cms import SiteBlock, SiteSettings, clear_site_blocks_cache
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


PLAQUE_KEYS = (
    ("about", "about_row_1_value"),
    ("about", "about_row_2_value"),
    ("about", "about_row_3_value"),
    ("about", "about_row_4_value"),
    ("about", "about_form_email_ph"),
    ("blog", "blog_ask_phone"),
    ("blog", "blog_ask_hours"),
    ("site", "info_consult_phone"),
    ("site", "info_consult_hours"),
)

# Старі дефолти-заглушки. Порівняння точне (і після strip країв).
PLAQUE_STUBS = frozenset(
    {
        "067 00 00 00",
        "067 00 00 00, 066 00 00 00",
        "xxx@gmail.com",
        "mail@example.com",
        "м. Київ, [вулиця, будинок]",
        "г. Киев, [улица, дом]",
        "Пн–Пт 9:00–19:00\nСб 10:00–17:00\nНд — вихідний",
        "Пн–Пт 9:00–19:00, Сб 10:00–17:00, Нд — вихідний",
        "Пн–Пт 9:00–19:00, Сб 10:00–17:00, Вс — выходной",
        "Пн–Пт 9:00–19:00\nСб 10:00–17:00\nВс — выходной",
        "Пн–Сб, 9:00–19:00",
    }
)


def _is_stub(value: str) -> bool:
    return value in PLAQUE_STUBS or value.strip() in PLAQUE_STUBS


def step_plaques(stdout, dry_run: bool) -> str:
    cleared = 0
    kept = 0
    missing = 0
    for page, key in PLAQUE_KEYS:
        block = SiteBlock.objects.filter(page=page, key=key).first()
        if block is None:
            missing += 1
            continue
        fields: list[str] = []
        if _is_stub(block.text_html or ""):
            block.text_html = ""
            fields.append("text_html")
        if _is_stub(block.text_html_ru or ""):
            block.text_html_ru = ""
            fields.append("text_html_ru")
        if not fields:
            kept += 1
            continue
        cleared += 1
        stdout.write(f"плашка {page}.{key}: очищено {', '.join(fields)}")
        if not dry_run:
            block.save(update_fields=fields)
    if cleared and not dry_run:
        clear_site_blocks_cache()
    line = f"плашки: очищено {cleared}, без заглушки {kept}, немає блоку {missing}"
    stdout.write(line)
    return line


STEPS = [step_email, step_hours_address, step_social, step_plaques]


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
