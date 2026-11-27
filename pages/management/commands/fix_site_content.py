"""Ідемпотентні правки контенту: лише хибні або порожні значення.

Не перетирає те, що власник уже змінив. --dry-run нічого не пише.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

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


PRICE_BLOCKS = (
    ("delivery", "delivery_row_1_c", frozenset({"80 ₴", "80"})),
    ("delivery", "delivery_row_2_c", frozenset({"150 ₴", "150"})),
    ("delivery", "delivery_row_3_c", frozenset({"Безкоштовно", "Бесплатно", "0"})),
)


def _price_is_stub(value: str, allowed: frozenset[str]) -> bool:
    text = (value or "").strip()
    return text == "" or text in allowed


def step_delivery_prices(stdout, dry_run: bool) -> str:
    removed = 0
    kept = 0
    for page, key, allowed in PRICE_BLOCKS:
        block = SiteBlock.objects.filter(page=page, key=key).first()
        if block is None:
            continue
        if _price_is_stub(block.text_html or "", allowed) and _price_is_stub(
            block.text_html_ru or "", allowed
        ):
            removed += 1
            stdout.write(
                f"ціна {page}.{key}: рядок не використовується (ціна з оформлення), не видаляю"
            )
        else:
            kept += 1
            stdout.write(f"ціна {page}.{key}: не чіпаю — текст змінено")
    if removed and not dry_run:
        clear_site_blocks_cache()
    line = f"ціни доставки: прибрано {removed}, залишено змінені {kept}"
    stdout.write(line)
    return line


def translate_product_names(stdout, dry_run: bool) -> str:
    from catalog.models import Category, Product
    from catalog.ru_names import has_ukrainian_leftover, translate_name

    def fill(model, label: str) -> tuple[int, int, int]:
        filled = 0
        kept = 0
        skipped = 0
        for obj in model.objects.all().only("pk", "name", "name_ru"):
            if (obj.name_ru or "").strip():
                kept += 1
                continue
            ru = translate_name(obj.name or "")
            if not ru:
                skipped += 1
                stdout.write(f"{label} {obj.pk}: порожня назва — пропуск")
                continue
            if has_ukrainian_leftover(ru):
                skipped += 1
                stdout.write(
                    f"{label} {obj.pk}: лишились українські літери — пропуск ({ru})"
                )
                continue
            filled += 1
            stdout.write(f"{label} {obj.pk}: name_ru ← {ru}")
            if dry_run:
                continue
            updated = model.objects.filter(pk=obj.pk, name_ru=obj.name_ru).update(
                name_ru=ru
            )
            if not updated:
                stdout.write(f"{label} {obj.pk}: name_ru вже змінено — не чіпаю")
        return filled, kept, skipped

    product_filled, product_kept, product_skipped = fill(Product, "товар")
    category_filled, category_kept, category_skipped = fill(Category, "категорія")
    line = (
        f"назви RU: товари заповнено {product_filled}, уже були {product_kept}, "
        f"пропуск {product_skipped}; категорії заповнено {category_filled}, "
        f"уже були {category_kept}, пропуск {category_skipped}"
    )
    stdout.write(line)
    return line


def step_brand_size_to_specs(stdout, dry_run: bool) -> str:
    """Поля brand/size_* → характеристики, якщо рядка атрибута ще немає."""
    from catalog.admin_product_filters import resolve_spec_value
    from catalog.models import Attribute, Product, ProductAttribute

    slug_attr = {}
    for slug in ('brand', 'length', 'size-ab'):
        attr = Attribute.objects.filter(slug=slug).first()
        if attr is None:
            stdout.write(f'атрибут «{slug}»: немає в БД — пропуск')
            continue
        slug_attr[slug] = attr

    existing = {
        slug: set(
            ProductAttribute.objects.filter(
                attribute_value__attribute__slug=slug
            ).values_list('product_id', flat=True)
        )
        for slug in slug_attr
    }
    created = 0
    existed = 0
    for product in Product.objects.only('id', 'brand', 'size_mm', 'size_a', 'size_b'):
        jobs = []
        brand = (product.brand or '').strip()
        if brand and 'brand' in slug_attr:
            jobs.append(('brand', brand))
        if product.size_mm and 'length' in slug_attr:
            jobs.append(('length', f'{product.size_mm}'))
        if product.size_a and product.size_b and 'size-ab' in slug_attr:
            jobs.append(('size-ab', f'{product.size_a}×{product.size_b}'))
        for slug, raw in jobs:
            if product.pk in existing[slug]:
                existed += 1
                continue
            created += 1
            if dry_run:
                continue
            value = resolve_spec_value(slug_attr[slug], raw)
            if value is None:
                continue
            ProductAttribute.objects.get_or_create(
                product=product, attribute_value=value
            )

    line = f'бренд/розміри → характеристики: створено {created}, уже були {existed}'
    stdout.write(line)
    return line


def step_review_avg(stdout, dry_run: bool) -> str:
    """Перерахувати reviews_avg лише там, де є опубліковані відгуки і значення інше."""
    from django.db.models import Avg

    from catalog.models import Product, Review
    from catalog.review_stats import quantize_review_avg

    rows = (
        Review.objects.filter(is_published=True)
        .values('product_id')
        .annotate(avg=Avg('rating'))
    )
    ids = [row['product_id'] for row in rows]
    products = Product.objects.in_bulk(ids)
    changed = 0
    for row in rows:
        product = products.get(row['product_id'])
        if product is None:
            continue
        new_avg = quantize_review_avg(row['avg'])
        if product.reviews_avg == new_avg:
            continue
        changed += 1
        if dry_run:
            continue
        Product.objects.filter(pk=product.pk).update(reviews_avg=new_avg)
    line = f'середня оцінка відгуків: оновлено {changed}'
    stdout.write(line)
    return line


STEPS = [
    step_email,
    step_hours_address,
    step_social,
    step_plaques,
    step_delivery_prices,
    translate_product_names,
    step_brand_size_to_specs,
    step_review_avg,
]


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
        else:
            with transaction.atomic():
                for step in STEPS:
                    step(self.stdout, dry_run)
        self.stdout.write(self.style.SUCCESS(f"Кроків: {len(STEPS)}"))
