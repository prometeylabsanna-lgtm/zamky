"""Генерація товарних фідів: один queryset → серіалізатори Google/Facebook (RSS 2.0 + g:) і Prom (YML).

Контракт полів і мапінг: docs/MARKETING_FEEDS.md.
XML будується лише через lxml (без строкових шаблонів), гроші — Decimal.
Закупівельна ціна, постачальник та внутрішні поля не виводяться ніколи.
"""

from __future__ import annotations

import hashlib
import html
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.core.cache import cache
from django.db.models import Prefetch
from django.utils import timezone, translation
from django.utils.html import strip_tags
from lxml import etree

from catalog.models import Category, Product, ProductAttribute, ProductImage
from marketing.models import ProductFeed, SeoSettings

G_NS = "http://base.google.com/ns/1.0"
VERSION_KEY = "marketing_feeds_version"
CENT = Decimal("0.01")
MAX_TITLE = 150
MAX_DESCRIPTION = 5000
MAX_ADDITIONAL_IMAGES = 10
GTIN_RE = re.compile(r"^(\d{8}|\d{12}|\d{13}|\d{14})$")
# Артикул Prom: до 25 символів; цифри, латиниця, кирилиця, -_./ і пробіл.
PROM_VENDOR_CODE_RE = re.compile(r"^[0-9A-Za-z\u0400-\u04FF\-_./ ]{1,25}$")
_WS_RE = re.compile(r"\s+")
# Символи, заборонені в XML 1.0 (керівні, крім \t \n \r).
_XML_BAD_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")


@dataclass
class FeedItem:
    id: str
    title: str
    description: str
    link: str
    image_link: str
    additional_image_links: list[str]
    price: Decimal
    sale_price: Decimal | None
    currency: str
    availability: str
    quantity: int
    condition: str
    brand: str
    gtin: str
    mpn: str
    identifier_exists: bool
    google_product_category: int | None
    product_type: str
    category_id: int
    params: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class FeedResult:
    items: list[FeedItem]
    included: int
    excluded: int
    reasons: dict[str, int]
    categories: dict[int, Category]
    warnings: dict[str, int] = field(default_factory=dict)


@dataclass
class FeedPayload:
    body: bytes
    etag: str
    last_modified: datetime
    included: int
    excluded: int
    reasons: dict[str, int]
    warnings: dict[str, int] = field(default_factory=dict)


# ---------- helpers ----------

def feeds_version() -> int:
    value = cache.get(VERSION_KEY)
    if value is None:
        value = 1
        cache.set(VERSION_KEY, value, None)
    return int(value)


def bump_feeds_version() -> None:
    try:
        cache.incr(VERSION_KEY)
    except ValueError:
        cache.set(VERSION_KEY, 2, None)


def money(value) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def format_price(value: Decimal, currency: str) -> str:
    return f"{money(value)} {currency}"


def prom_vendor_code(sku: str) -> str | None:
    """Повертає sku, якщо він підходить як vendorCode Prom, інакше None."""
    value = sku or ""
    if PROM_VENDOR_CODE_RE.fullmatch(value):
        return value
    return None


def clean_text(value: str, limit: int, *, strip_html: bool = True) -> str:
    text = value or ""
    if strip_html:
        text = strip_tags(text)
    text = html.unescape(text)
    text = _XML_BAD_RE.sub("", text)
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit].rstrip()


def resolve_base_url(request=None) -> str:
    domain = (SeoSettings.load().primary_domain or "").strip().rstrip("/")
    if domain:
        return domain
    if request is not None:
        return f"{request.scheme}://{request.get_host()}"
    return ""


def _absolute(base: str, url: str) -> str:
    if not url:
        return ""
    if url.startswith("https://") or url.startswith("http://"):
        return url
    return f"{base}{url if url.startswith('/') else '/' + url}"


def _category_maps():
    cats = {c.pk: c for c in Category.objects.only("id", "name", "parent_id", "is_active", "slug")}
    children: dict[int, list[int]] = {}
    for c in cats.values():
        if c.parent_id:
            children.setdefault(c.parent_id, []).append(c.pk)
    return cats, children


def _descendants(root_ids, children) -> set[int]:
    out: set[int] = set()
    stack = list(root_ids)
    while stack:
        cid = stack.pop()
        if cid in out:
            continue
        out.add(cid)
        stack.extend(children.get(cid, []))
    return out


def _ancestors(cat_id: int, cats) -> list[Category]:
    chain = []
    seen = set()
    current = cats.get(cat_id)
    while current is not None and current.pk not in seen:
        seen.add(current.pk)
        chain.append(current)
        current = cats.get(current.parent_id) if current.parent_id else None
    return list(reversed(chain))


def base_queryset():
    return (
        Product.objects.filter(is_active=True)
        .select_related("category", "family")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("sort_order", "id")),
            Prefetch(
                "product_attributes",
                queryset=ProductAttribute.objects.select_related("attribute_value__attribute"),
            ),
        )
        .order_by("catalog_order", "pk")
    )


def collect_items(feed: ProductFeed, base_url: str) -> FeedResult:
    cats, children = _category_maps()
    mapping = {m.category_id: m.google_product_category for m in feed.category_mappings.all()}
    qs = base_queryset()
    selected = list(feed.categories.values_list("pk", flat=True))
    if selected:
        qs = qs.filter(category_id__in=_descendants(selected, children))
    if feed.only_in_stock:
        qs = qs.filter(stock__gt=0)

    reasons: Counter = Counter()
    items: list[FeedItem] = []
    used_cats: set[int] = set()
    with translation.override("ua"):
        for p in qs.iterator(chunk_size=500):
            reason = _exclude_reason(p, cats)
            if reason:
                reasons[reason] += 1
                continue
            images = [
                _absolute(base_url, _safe_url(img.image)) for img in p.images.all() if img.image
            ]
            images = [u for u in images if u]
            link = _absolute(base_url, p.get_absolute_url())
            if not images:
                reasons["no_image"] += 1
                continue
            if not link:
                reasons["no_link"] += 1
                continue
            price = money(p.price)
            sale = None
            if p.old_price and money(p.old_price) > price:
                sale = price
                price = money(p.old_price)
            chain = _ancestors(p.category_id, cats)
            gpc = None
            for c in reversed(chain):
                if c.pk in mapping:
                    gpc = mapping[c.pk]
                    break
            brand = (p.brand or (p.family.brand if p.family_id and p.family else "") or "").strip()
            gtin = (getattr(p, "gtin", "") or "").strip()
            if not GTIN_RE.match(gtin):
                gtin = ""
            mpn = (getattr(p, "mpn", "") or "").strip()
            params = [
                (pa.attribute_value.attribute.name, pa.attribute_value.value)
                for pa in p.product_attributes.all()
            ]
            used_cats.update(c.pk for c in chain)
            items.append(
                FeedItem(
                    id=p.sku,
                    title=clean_text(p.name, MAX_TITLE),
                    description=clean_text(
                        p.description or p.short_description or p.name, MAX_DESCRIPTION
                    ),
                    link=link,
                    image_link=images[0],
                    additional_image_links=images[1 : 1 + MAX_ADDITIONAL_IMAGES],
                    price=price,
                    sale_price=sale,
                    currency=feed.currency,
                    availability="in_stock" if p.stock > 0 else "out_of_stock",
                    quantity=max(int(p.stock), 0),
                    condition="new",
                    brand=brand,
                    gtin=gtin,
                    mpn=mpn,
                    identifier_exists=bool(gtin or (brand and mpn)),
                    google_product_category=gpc,
                    product_type=" > ".join(c.name for c in chain),
                    category_id=p.category_id,
                    params=params,
                )
            )
    return FeedResult(
        items=items,
        included=len(items),
        excluded=sum(reasons.values()),
        reasons=dict(reasons),
        categories={cid: cats[cid] for cid in used_cats if cid in cats},
    )


def _safe_url(fieldfile) -> str:
    try:
        return fieldfile.url
    except Exception:
        return ""


def _exclude_reason(p: Product, cats) -> str:
    if p.price is None or money(p.price) <= 0:
        return "price_not_positive"
    cost = getattr(p, "purchase_price", None)  # у каталозі зараз немає; хук на майбутнє
    if cost is not None and money(cost) > money(p.price):
        return "below_purchase_price"
    cat = cats.get(p.category_id)
    if cat is not None and not cat.is_active:
        return "inactive_category"
    if not p.slug:
        return "no_link"
    return ""


# ---------- serializers ----------

def _sub(parent, tag, text=None, ns=None, **attrs):
    el = etree.SubElement(parent, f"{{{ns}}}{tag}" if ns else tag, **attrs)
    if text is not None:
        el.text = _XML_BAD_RE.sub("", str(text))
    return el


def build_rss(feed: ProductFeed, result: FeedResult, base_url: str) -> bytes:
    rss = etree.Element("rss", nsmap={"g": G_NS}, version="2.0")
    channel = _sub(rss, "channel")
    _sub(channel, "title", feed.shop_name or feed.name)
    _sub(channel, "link", f"{base_url}/" if base_url else "")
    _sub(channel, "description", feed.shop_name or feed.name)
    for it in result.items:
        item = _sub(channel, "item")
        _sub(item, "id", it.id, ns=G_NS)
        _sub(item, "title", it.title, ns=G_NS)
        _sub(item, "description", it.description, ns=G_NS)
        _sub(item, "link", it.link, ns=G_NS)
        _sub(item, "image_link", it.image_link, ns=G_NS)
        for extra in it.additional_image_links:
            _sub(item, "additional_image_link", extra, ns=G_NS)
        _sub(item, "availability", it.availability, ns=G_NS)
        _sub(item, "price", format_price(it.price, it.currency), ns=G_NS)
        if it.sale_price is not None:
            _sub(item, "sale_price", format_price(it.sale_price, it.currency), ns=G_NS)
        _sub(item, "condition", it.condition, ns=G_NS)
        if it.brand:
            _sub(item, "brand", it.brand, ns=G_NS)
        if it.gtin:
            _sub(item, "gtin", it.gtin, ns=G_NS)
        if it.mpn:
            _sub(item, "mpn", it.mpn, ns=G_NS)
        if not it.identifier_exists:
            _sub(item, "identifier_exists", "no", ns=G_NS)
        if it.google_product_category:
            _sub(item, "google_product_category", it.google_product_category, ns=G_NS)
        if it.product_type:
            _sub(item, "product_type", it.product_type, ns=G_NS)
    return etree.tostring(rss, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def _cdata(text: str):
    # "]]>" не може бути всередині CDATA.
    return etree.CDATA(_XML_BAD_RE.sub("", text).replace("]]>", "]] >"))


def build_yml(feed: ProductFeed, result: FeedResult, base_url: str) -> bytes:
    now = timezone.localtime()
    root = etree.Element("yml_catalog", date=now.strftime("%Y-%m-%d %H:%M"))
    shop = _sub(root, "shop")
    _sub(shop, "name", feed.shop_name or feed.name)
    _sub(shop, "company", feed.company_name or feed.shop_name or feed.name)
    _sub(shop, "url", f"{base_url}/" if base_url else "")
    currencies = _sub(shop, "currencies")
    _sub(currencies, "currency", id=feed.currency, rate="1")
    categories = _sub(shop, "categories")
    for cat in sorted(result.categories.values(), key=lambda c: c.pk):
        attrs = {"id": str(cat.pk)}
        if cat.parent_id and cat.parent_id in result.categories:
            attrs["parentId"] = str(cat.parent_id)
        _sub(categories, "category", cat.name, **attrs)
    offers = _sub(shop, "offers")
    for it in result.items:
        offer = _sub(
            offers, "offer", id=it.id, available="true" if it.availability == "in_stock" else "false"
        )
        _sub(offer, "url", it.link)
        current = it.sale_price if it.sale_price is not None else it.price
        _sub(offer, "price", str(money(current)))
        # <price_old> лише коли стара ціна вища за продажну і товар у наявності.
        # <discount> не виводимо: у Prom він має пріоритет над старою ціною.
        if (
            it.sale_price is not None
            and it.availability == "in_stock"
            and it.price > it.sale_price
        ):
            _sub(offer, "price_old", str(money(it.price)))
        _sub(offer, "currencyId", it.currency)
        _sub(offer, "categoryId", str(it.category_id))
        for pic in [it.image_link, *it.additional_image_links]:
            _sub(offer, "picture", pic)
        _sub(offer, "name", it.title)
        if it.brand:
            _sub(offer, "vendor", it.brand)
        vendor_code = prom_vendor_code(it.id)
        if vendor_code is not None:
            _sub(offer, "vendorCode", vendor_code)
        desc = _sub(offer, "description")
        desc.text = _cdata(it.description)
        for name, value in it.params:
            _sub(offer, "param", value, name=name)
        _sub(offer, "quantity_in_stock", str(it.quantity))
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def _prom_warnings(items: list[FeedItem]) -> dict[str, int]:
    n = sum(1 for it in items if prom_vendor_code(it.id) is None)
    return {"vendorcode_invalid": n} if n else {}


def render_feed(feed: ProductFeed, base_url: str) -> tuple[bytes, FeedResult]:
    result = collect_items(feed, base_url)
    if feed.feed_type == ProductFeed.FeedType.PROM:
        result.warnings = _prom_warnings(result.items)
        body = build_yml(feed, result, base_url)
    else:
        body = build_rss(feed, result, base_url)
    return body, result


def _cache_key(feed: ProductFeed, base_url: str) -> str:
    stamp = int(feed.updated_at.timestamp()) if feed.updated_at else 0
    base_hash = hashlib.sha1(base_url.encode()).hexdigest()[:8]
    return f"marketing_feed:{feed.pk}:{stamp}:{feeds_version()}:{base_hash}"


def get_feed_payload(feed: ProductFeed, base_url: str, *, force: bool = False) -> FeedPayload:
    key = _cache_key(feed, base_url)
    if not force:
        cached = cache.get(key)
        if cached is not None:
            return cached
    body, result = render_feed(feed, base_url)
    payload = FeedPayload(
        body=body,
        etag='"' + hashlib.sha256(body).hexdigest()[:32] + '"',
        last_modified=timezone.now().replace(microsecond=0),
        included=result.included,
        excluded=result.excluded,
        reasons=result.reasons,
        warnings=result.warnings,
    )
    cache.set(key, payload, max(1, min(6, feed.cache_hours or 3)) * 3600)
    # Статистика для адмінки; update() не чіпає updated_at → кеш-ключ стабільний.
    ProductFeed.objects.filter(pk=feed.pk).update(
        last_generated_at=payload.last_modified,
        last_included=payload.included,
        last_excluded=payload.excluded,
        last_excluded_reasons=payload.reasons,
        last_warnings=payload.warnings,
    )
    return payload
