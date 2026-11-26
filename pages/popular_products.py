"""Дефолти та вибірка товарів «Популярні» на головній."""

from __future__ import annotations

from django.db.models import F

from catalog.category_tree import TYPE_ROOT_NAMES, subtree_ids
from catalog.models import Category, Product
from pages.models_cms import SiteBlock
from pages.models_popular import HomePopularProduct

READY_PAGE = "home"
READY_KEY = "popular_lists_ready"
POPULAR_LIMIT = 8
DEMO_SKU_PREFIX = "HOME-"
POPULAR_TYPE_ROOT = TYPE_ROOT_NAMES[5]

POPULAR_TABS: tuple[tuple[str, str], ...] = (
    (HomePopularProduct.Tab.HITS, "Вкладка «Хіти»"),
    (HomePopularProduct.Tab.NEWS, "Вкладка «Новинки»"),
    (HomePopularProduct.Tab.SALES, "Вкладка «Знижки»"),
)


def popular_queryset():
    return HomePopularProduct.objects.select_related("product").order_by(
        "tab", "sort_order", "pk"
    )


def _lists_ready() -> bool:
    block = SiteBlock.objects.filter(page=READY_PAGE, key=READY_KEY).first()
    return bool(block and (block.text_html or "").strip() == "1")


def mark_popular_lists_ready() -> None:
    SiteBlock.objects.update_or_create(
        page=READY_PAGE,
        key=READY_KEY,
        defaults={
            "label": READY_KEY,
            "content_type": SiteBlock.ContentType.TEXT,
            "text_html": "1",
        },
    )


def _catalog_qs():
    return (
        Product.objects.filter(is_active=True)
        .exclude(sku__startswith=DEMO_SKU_PREFIX)
        .select_related("category", "category__parent", "category__parent__parent")
    )


def _root_key(product) -> str:
    category = getattr(product, "category", None)
    seen = set()
    while category is not None and category.pk not in seen:
        seen.add(category.pk)
        if not category.parent_id:
            return f"r:{category.pk}"
        category = category.parent
    return f"p:{product.pk}"


def _product_name_key(product) -> str:
    family_id = getattr(product, "family_id", None)
    if family_id:
        return f"f:{family_id}"
    return (product.name or "").strip() or f"id:{product.pk}"


def _type_root_ids(name: str = POPULAR_TYPE_ROOT) -> list[int]:
    root = (
        Category.objects.filter(name=name, parent__isnull=True).first()
        or Category.objects.filter(name=name).first()
    )
    if root is None:
        return []
    return list(subtree_ids(root.pk))


def _diverse(products, limit: int) -> list[Product]:
    picked: list[Product] = []
    seen_name: set[str] = set()
    seen_root: set[str] = set()
    rest: list[Product] = []
    for product in products:
        name = _product_name_key(product)
        if name in seen_name:
            continue
        root = _root_key(product)
        if root in seen_root:
            rest.append(product)
            continue
        seen_root.add(root)
        seen_name.add(name)
        picked.append(product)
        if len(picked) >= limit:
            return picked
    for product in rest:
        name = _product_name_key(product)
        if name in seen_name:
            continue
        seen_name.add(name)
        picked.append(product)
        if len(picked) >= limit:
            break
    return picked


def _is_demo_clone_set(products: list[Product]) -> bool:
    if not products:
        return False
    if all((p.sku or "").startswith(DEMO_SKU_PREFIX) for p in products):
        return True
    names = {_product_name_key(p) for p in products}
    return len(products) > 1 and len(names) == 1


def _tab_candidates(qs, tab: str) -> list[Product]:
    if tab == HomePopularProduct.Tab.HITS:
        rows = list(qs.filter(is_hit=True).order_by("catalog_order", "pk")[:80])
        if rows:
            return rows
        return list(qs.order_by("catalog_order", "pk")[:80])
    if tab == HomePopularProduct.Tab.NEWS:
        rows = list(qs.filter(is_new=True).order_by("catalog_order", "pk")[:80])
        if rows:
            return rows
        return list(qs.order_by("-created_at")[:80])
    rows = list(
        qs.filter(old_price__gt=F("price")).order_by("catalog_order", "pk")[:80]
    )
    if rows:
        return rows
    return _tab_candidates(qs, HomePopularProduct.Tab.HITS)


def _auto_products(tab: str, limit: int = 8) -> list[Product]:
    qs = _catalog_qs()
    type_ids = _type_root_ids()
    picked: list[Product] = []
    if type_ids:
        typed = _tab_candidates(qs.filter(category_id__in=type_ids), tab)
        picked = _diverse(typed, limit)
        if len(picked) >= limit:
            return picked
    rest = _tab_candidates(qs, tab)
    seen = {product.pk for product in picked}
    picked.extend(_diverse([p for p in rest if p.pk not in seen], limit - len(picked)))
    return picked[:limit]


def _seed_from_auto() -> int:
    created = 0
    for tab, _title in POPULAR_TABS:
        for index, product in enumerate(_auto_products(tab)):
            _, was_created = HomePopularProduct.objects.get_or_create(
                tab=tab,
                product=product,
                defaults={"sort_order": index + 1, "is_active": True},
            )
            if was_created:
                created += 1
    return created


def ensure_default_popular() -> int:
    if _lists_ready():
        return 0
    created = _seed_from_auto()
    mark_popular_lists_ready()
    return created


def reset_demo_popular() -> int:
    HomePopularProduct.objects.all().delete()
    SiteBlock.objects.filter(page=READY_PAGE, key=READY_KEY).delete()
    return ensure_default_popular()


def products_for_tab(tab: str, limit: int = POPULAR_LIMIT) -> list[Product]:
    ensure_default_popular()
    rows = (
        HomePopularProduct.objects.filter(tab=tab, is_active=True)
        .select_related(
            "product",
            "product__category",
            "product__category__parent",
            "product__category__parent__parent",
        )
        .prefetch_related("product__images")
        .order_by("sort_order", "pk")[:24]
    )
    slotted: list[Product] = []
    for row in rows:
        product = row.product
        if product is None or not product.is_active:
            continue
        slotted.append(product)
    if not slotted:
        return []
    if _is_demo_clone_set(slotted):
        auto = _auto_products(tab, limit)
        if auto:
            return auto
    return _diverse(slotted, limit)


def get_home_popular() -> dict[str, list[Product]]:
    return {
        "hits": products_for_tab(HomePopularProduct.Tab.HITS),
        "news": products_for_tab(HomePopularProduct.Tab.NEWS),
        "sales": products_for_tab(HomePopularProduct.Tab.SALES),
    }
