"""Ідемпотентний сід маркетингу (та сама модель, що й адмінка)."""

import secrets

DEFAULT_TITLE = "Центр замків"  # колишній хардкод <title> у base.html
DEFAULT_SHOP = "Центр замків"
FEED_DEFAULTS = (
    ("google", "Google Merchant"),
    ("facebook", "Facebook / Meta Catalog"),
    ("prom", "Prom.ua"),
)


def seed_marketing(SeoSettings, TrackingSettings, ProductFeed, SiteSettings=None) -> dict:
    stats = {"seo": 0, "tracking": 0, "feeds": 0}
    seo, created = SeoSettings.objects.get_or_create(pk=1)
    stats["seo"] = int(created)
    changed = False
    if not seo.title_default:
        seo.title_default = DEFAULT_TITLE
        changed = True
    site = SiteSettings.objects.filter(pk=1).first() if SiteSettings is not None else None
    if site is not None:
        for src, dst in (
            ("meta_title_ru", "title_default_ru"),
            ("meta_description", "description_default"),
            ("meta_description_ru", "description_default_ru"),
        ):
            value = (getattr(site, src, "") or "").strip()
            if value and not getattr(seo, dst):
                setattr(seo, dst, value)
                changed = True
        meta_title = (site.meta_title or "").strip()
        if meta_title and seo.title_default == DEFAULT_TITLE:
            seo.title_default = meta_title
            changed = True
    if changed:
        seo.save()
    _, created = TrackingSettings.objects.get_or_create(pk=1)
    stats["tracking"] = int(created)
    for feed_type, name in FEED_DEFAULTS:
        if ProductFeed.objects.filter(feed_type=feed_type).exists():
            continue
        ProductFeed.objects.create(
            name=name,
            feed_type=feed_type,
            slug=f"{feed_type}-{secrets.token_hex(8)}",
            is_enabled=False,
            shop_name=DEFAULT_SHOP,
            company_name=DEFAULT_SHOP if feed_type == "prom" else "",
            currency="UAH",
        )
        stats["feeds"] += 1
    return stats
