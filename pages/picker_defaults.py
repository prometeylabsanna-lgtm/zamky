"""Стартові двері/фільтри підбору + читання для головної."""

from __future__ import annotations

from decimal import Decimal

from django.templatetags.static import static

from pages.models_picker import PickerDoor, PickerFilter, PickerFilterOption

DEFAULT_DOORS = (
    ("0", "Вхідні", "Входные", "двері", "двери", "img/v2/p2_14.png", "Замки,захист"),
    ("1", "Міжкімнатні", "Межкомнатные", "двері", "двери", "img/v2/p2_15.png", "Серцевини,циліндр"),
    ("2", "Металеві", "Металлические", "двері", "двери", "img/v2/p2_16.png", "Замки,захист"),
    ("3", "Пластикові", "Пластиковые", "двері", "двери", "img/v2/p2_17.png", "Серцевини"),
    ("4", "Металеві", "Металлические", "електро", "электро", "img/v2/p2_18.png", "код,елект"),
)

DEFAULT_FILTERS = (
    ("mech", "Тип замка", "Тип замка", 0),
    ("brand", "Бренд", "Бренд", 1),
    ("price", "Ціновий діапазон", "Ценовой диапазон", 2),
    ("color", "Колір/покриття", "Цвет/покрытие", 3),
)

DEFAULT_PRICE = (
    ("до 1500 ₴", Decimal("0"), Decimal("1500")),
    ("1500 – 3000 ₴", Decimal("1500"), Decimal("3000")),
    ("3000 – 4500 ₴", Decimal("3000"), Decimal("4500")),
    ("від 4500 ₴", Decimal("4500"), None),
)

FALLBACK_MECH = ("Циліндровий", "Сувальдний", "Електромеханічний")
FALLBACK_COLOR = ("Латунь", "Нікель", "Хром")
FALLBACK_BRAND = ("ABARO", "Mottura", "Cisa", "Kale", "Apecs")


def ensure_picker_defaults() -> None:
    if not PickerDoor.objects.exists():
        for i, row in enumerate(DEFAULT_DOORS):
            code, l1, l1r, l2, l2r, fallback, hints = row
            PickerDoor.objects.create(
                code=code,
                label_line1=l1,
                label_line1_ru=l1r,
                label_line2=l2,
                label_line2_ru=l2r,
                static_fallback=fallback,
                match_hints=hints,
                sort_order=i,
                is_active=True,
            )
    if not PickerFilter.objects.exists():
        for key, label, label_ru, order in DEFAULT_FILTERS:
            PickerFilter.objects.create(
                key=key, label=label, label_ru=label_ru, sort_order=order, is_active=True
            )
        _seed_filter_options()
    _link_picker_catalog()


def _seed_filter_options() -> None:
    by_key = {item.key: item for item in PickerFilter.objects.all()}
    _fill_attr_options(by_key.get("mech"), "mech", FALLBACK_MECH)
    _fill_attr_options(by_key.get("color"), "color", FALLBACK_COLOR)
    _fill_brands(by_key.get("brand"))
    price = by_key.get("price")
    if price is not None and not price.options.exists():
        for i, (label, lo, hi) in enumerate(DEFAULT_PRICE):
            PickerFilterOption.objects.create(
                filter=price,
                label=label,
                value=label,
                price_min=lo,
                price_max=hi,
                sort_order=i,
                is_active=True,
            )


def _fill_attr_options(filt, slug: str, fallback: tuple[str, ...]) -> None:
    if filt is None or filt.options.exists():
        return
    values: list[str] = []
    try:
        from catalog.models import AttributeValue

        rows = list(
            AttributeValue.objects.filter(attribute__slug=slug)
            .order_by("sort_order", "value")
            .values("value", "slug")
            .distinct()
        )
    except Exception:
        rows = []
    if not rows:
        rows = [{"value": label, "slug": label} for label in fallback]
    for i, row in enumerate(rows):
        PickerFilterOption.objects.create(
            filter=filt,
            label=row["value"],
            value=row["slug"] or row["value"],
            sort_order=i,
            is_active=True,
        )


def _fill_brands(filt) -> None:
    if filt is None or filt.options.exists():
        return
    brands: list[str] = []
    try:
        from catalog.models import Product

        brands = list(
            Product.objects.filter(is_active=True)
            .exclude(brand="")
            .order_by("brand")
            .values_list("brand", flat=True)
            .distinct()
        )
    except Exception:
        brands = []
    if not brands:
        brands = list(FALLBACK_BRAND)
    for i, brand in enumerate(brands):
        PickerFilterOption.objects.create(
            filter=filt,
            label=brand,
            value=brand,
            sort_order=i,
            is_active=True,
        )


def _pick(lang: str, ua: str, ru: str) -> str:
    if lang == "ru" and (ru or "").strip():
        return ru
    return ua or ""


def door_image_url(door: PickerDoor) -> tuple[str, str]:
    if door.image:
        try:
            return door.image.url, ""
        except Exception:
            pass
    fallback = door.static_fallback or "img/v2/p2_14.png"
    return "", fallback


def get_home_doors(lang: str = "ua") -> list[dict]:
    ensure_picker_defaults()
    rows = []
    for door in PickerDoor.objects.filter(is_active=True).order_by("sort_order", "pk"):
        image_url, fallback = door_image_url(door)
        rows.append(
            {
                "id": door.code,
                "image": fallback,
                "image_url": image_url,
                "line1": door.line1(lang),
                "line2": door.line2(lang),
            }
        )
    return rows


def get_picker_filters(lang: str = "ua") -> list[dict]:
    ensure_picker_defaults()
    rows = []
    for filt in PickerFilter.objects.filter(is_active=True).order_by("sort_order", "pk"):
        rows.append({"key": filt.key, "label": filt.display_label(lang)})
    return rows


def get_picker_options_json(lang: str = "ua") -> dict[str, list[dict]]:
    ensure_picker_defaults()
    payload: dict[str, list[dict]] = {}
    qs = PickerFilter.objects.filter(is_active=True).prefetch_related("options")
    for filt in qs.order_by("sort_order", "pk"):
        opts = []
        for opt in filt.options.filter(is_active=True).order_by("sort_order", "pk"):
            opts.append({"label": opt.display_label(lang), "slug": opt.value})
        payload[filt.key] = opts
    return payload


def _link_picker_catalog() -> None:
    try:
        from catalog.models import Attribute, Category
    except Exception:
        return
    for door in PickerDoor.objects.all():
        if door.categories.exists():
            continue
        hints = [
            part.strip()
            for part in (door.match_hints or "").split(",")
            if part.strip()
        ]
        if not hints:
            continue
        from django.db.models import Q

        query = Q()
        for hint in hints:
            query |= Q(name__icontains=hint)
        cats = list(Category.objects.filter(query))
        if cats:
            door.categories.set(cats)
    for filt in PickerFilter.objects.filter(attribute_id=None).exclude(key="price"):
        attr = Attribute.objects.filter(slug=filt.key).first()
        if attr is not None:
            filt.attribute = attr
            filt.save(update_fields=["attribute"])


def fill_options_from_attribute(filt: PickerFilter) -> None:
    if filt is None or filt.attribute_id is None or filt.options.exists():
        return
    values = filt.attribute.values.order_by("sort_order", "value")
    for i, row in enumerate(values):
        PickerFilterOption.objects.create(
            filter=filt,
            label=(row.value or "")[:80],
            value=(row.slug or row.value or "")[:80],
            sort_order=i,
            is_active=True,
        )


def door_category_ids(raw: str) -> list[int]:
    ensure_picker_defaults()
    raw = (raw or "").strip()
    if not raw:
        return []
    door = PickerDoor.objects.filter(code__iexact=raw).first()
    if door is None and raw.isdigit():
        door = PickerDoor.objects.filter(code=raw).first()
    if door is None:
        return []
    ids = set(door.categories.values_list("pk", flat=True))
    if not ids:
        return []
    try:
        from catalog.models import Category
    except Exception:
        return list(ids)
    children = Category.objects.filter(parent_id__in=ids).values_list("pk", flat=True)
    ids.update(children)
    nested = Category.objects.filter(parent_id__in=ids).values_list("pk", flat=True)
    ids.update(nested)
    return list(ids)


def door_hints(raw: str) -> list[str]:
    ensure_picker_defaults()
    raw = (raw or "").strip()
    if not raw:
        return []
    door = PickerDoor.objects.filter(code__iexact=raw).first()
    if door is None and raw.isdigit():
        door = PickerDoor.objects.filter(code=raw).first()
    if door is None:
        return []
    return [part.strip() for part in (door.match_hints or "").split(",") if part.strip()]


def price_band(label: str) -> tuple[Decimal | None, Decimal | None] | None:
    ensure_picker_defaults()
    label = (label or "").strip()
    if not label:
        return None
    opt = (
        PickerFilterOption.objects.filter(filter__key="price", is_active=True)
        .filter(value=label)
        .first()
    )
    if opt is None:
        opt = PickerFilterOption.objects.filter(
            filter__key="price", is_active=True, label=label
        ).first()
    if opt is None:
        return None
    return (opt.price_min, opt.price_max)
