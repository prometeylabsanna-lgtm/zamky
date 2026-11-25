"""Дефолти та вибірка товарів «Популярні» на головній."""

from __future__ import annotations

from django.db.models import F

from catalog.models import Product
from pages.models_cms import SiteBlock
from pages.models_popular import HomePopularProduct

READY_PAGE = "home"
READY_KEY = "popular_lists_ready"
POPULAR_LIMIT = 24

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


def _auto_products(tab: str, limit: int = 8) -> list[Product]:
    qs = Product.objects.filter(is_active=True)
    if tab == HomePopularProduct.Tab.HITS:
        rows = list(qs.filter(is_hit=True).order_by("catalog_order", "pk")[:limit])
        if not rows:
            rows = list(qs.order_by("catalog_order", "pk")[:limit])
        return rows
    if tab == HomePopularProduct.Tab.NEWS:
        rows = list(qs.filter(is_new=True).order_by("catalog_order", "pk")[:limit])
        if not rows:
            rows = list(qs.order_by("-created_at")[:limit])
        return rows
    rows = list(
        qs.filter(old_price__gt=F("price")).order_by("catalog_order", "pk")[:limit]
    )
    if not rows:
        rows = _auto_products(HomePopularProduct.Tab.HITS, limit)
    return rows


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
        .select_related("product")
        .prefetch_related("product__images")
        .order_by("sort_order", "pk")[:limit]
    )
    out: list[Product] = []
    for row in rows:
        product = row.product
        if product is None or not product.is_active:
            continue
        out.append(product)
    return out


def get_home_popular() -> dict[str, list[Product]]:
    return {
        "hits": products_for_tab(HomePopularProduct.Tab.HITS),
        "news": products_for_tab(HomePopularProduct.Tab.NEWS),
        "sales": products_for_tab(HomePopularProduct.Tab.SALES),
    }
