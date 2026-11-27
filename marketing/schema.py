"""JSON-LD Product і BreadcrumbList лише з реальних полів."""

from __future__ import annotations

from decimal import Decimal

from django.urls import reverse

from marketing.seo import _abs, jsonld_script, localized
from marketing.seo_index import route_of
from pages.i18n_lib import tr


def _product_name(product, lang: str) -> str:
    card = getattr(product, "card_name", None)
    if callable(card):
        return card(lang) or product.name
    return localized(product.name, getattr(product, "name_ru", ""), lang) or product.name


def _product_image(product, domain: str) -> str:
    og = getattr(product, "og_image", None)
    if og:
        try:
            if og.url:
                return _abs(domain, og.url)
        except Exception:
            pass
    images = getattr(product, "images", None)
    if images is None:
        return ""
    try:
        first = images.all()[0]
    except Exception:
        first = None
    if first is None:
        try:
            first = images.first()
        except Exception:
            first = None
    if first is None:
        return ""
    try:
        url = first.image.url
    except Exception:
        return ""
    return _abs(domain, url) if url else ""


def product_jsonld(product, domain: str, lang: str, review_stats: dict | None) -> str:
    if not domain or product is None:
        return ""
    name = _product_name(product, lang)
    path = product.get_absolute_url()
    url = _abs(domain, path)
    price = product.price
    if isinstance(price, Decimal):
        price_s = format(price, "f")
    else:
        price_s = str(price)
    data: dict = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "sku": product.sku,
        "url": url,
        "offers": {
            "@type": "Offer",
            "url": url,
            "price": price_s,
            "priceCurrency": "UAH",
            "availability": (
                "https://schema.org/InStock"
                if int(product.stock or 0) > 0
                else "https://schema.org/OutOfStock"
            ),
        },
    }
    image = _product_image(product, domain)
    if image:
        data["image"] = image
    from catalog.product_specs import product_brand

    brand = product_brand(product)
    if brand:
        data["brand"] = {"@type": "Brand", "name": brand}
    stats = review_stats or {}
    if stats.get("from_reviews") and int(stats.get("count") or 0) > 0:
        data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(stats.get("rating")),
            "reviewCount": str(int(stats["count"])),
            "bestRating": "5",
            "worstRating": "1",
        }
    return jsonld_script(data)


def article_jsonld(post, domain: str, lang: str) -> str:
    if not domain or post is None:
        return ""
    title = post.card_title(lang) if hasattr(post, "card_title") else (getattr(post, "title", "") or "")
    title = (title or "").strip()
    if not title:
        return ""
    url = _abs(domain, post.get_absolute_url())
    data: dict = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "inLanguage": "ru" if lang == "ru" else "uk",
        "mainEntityOfPage": url,
        "url": url,
    }
    excerpt = ""
    if hasattr(post, "card_excerpt"):
        excerpt = (post.card_excerpt(lang) or "").strip()
    if excerpt:
        data["description"] = excerpt
    created = getattr(post, "created_at", None)
    if created is not None:
        data["datePublished"] = created.isoformat()
    updated = getattr(post, "updated_at", None)
    if updated is not None:
        data["dateModified"] = updated.isoformat()
    cover = getattr(post, "cover", None)
    if cover:
        try:
            if cover.url:
                data["image"] = _abs(domain, cover.url)
        except Exception:
            pass
    return jsonld_script(data)


def _crumb(name: str, url: str) -> dict:
    return {"name": name, "url": url}


def breadcrumb_items(request, context, domain: str, lang: str) -> list[dict]:
    if not domain or request is None:
        return []
    ns, name = route_of(request)
    home = _crumb(tr("Головна"), _abs(domain, reverse("catalog:home")))
    if ns == "catalog" and name == "product":
        product = context.get("product")
        if product is None:
            return []
        return [
            home,
            _crumb(tr("Каталог товарів"), _abs(domain, reverse("catalog:catalog"))),
            _crumb(_product_name(product, lang), _abs(domain, request.path)),
        ]
    if ns == "catalog" and name in ("catalog", "category"):
        title = (context.get("title") or "").strip() or tr("Каталог товарів")
        items = [home, _crumb(tr("Каталог товарів"), _abs(domain, reverse("catalog:catalog")))]
        if name == "category" or title:
            items.append(_crumb(title, _abs(domain, request.path)))
        return items
    if ns == "pages" and name in ("info", "info_page"):
        label = (context.get("page_name") or "").strip()
        if not label:
            return []
        return [home, _crumb(label, _abs(domain, request.path))]
    if ns == "pages" and name == "blog_list":
        label = (context.get("blog_title") or context.get("page_name") or "").strip()
        if not label:
            return []
        return [home, _crumb(label, _abs(domain, request.path))]
    if ns == "pages" and name == "blog_detail":
        post = context.get("post")
        if post is None:
            return []
        blog_label = (context.get("blog_title") or context.get("page_name") or tr("Корисне для вибору")).strip()
        return [
            home,
            _crumb(blog_label, _abs(domain, reverse("pages:blog_list"))),
            _crumb(
                post.card_title(lang) if hasattr(post, "card_title") else post.title,
                _abs(domain, request.path),
            ),
        ]
    return []


def breadcrumb_jsonld(request, context, domain: str, lang: str) -> str:
    items = breadcrumb_items(request, context, domain, lang)
    if len(items) < 2:
        return ""
    elements = []
    for i, item in enumerate(items, start=1):
        elements.append(
            {
                "@type": "ListItem",
                "position": i,
                "name": item["name"],
                "item": item["url"],
            }
        )
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": elements,
    }
    return jsonld_script(data)
