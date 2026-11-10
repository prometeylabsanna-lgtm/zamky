"""CONTENT_MANIFEST — SSOT слотів Full-CMS (Замки).

G3 SSOT. Режим surface → mode зафіксовано в G1.
Новий слот: спочатку сюди, потім registry/defaults/seed/frontend.
"""

from __future__ import annotations

# site_type / job / ownership (G0)
SITE_TYPE = "shop"
JOB_TYPE = "retrofit_hardcode_kill"
OWNERSHIP = "full"
LANGUAGES = ("ua", "ru")  # код вітрини; вкладки адмінки: Українська / Російська
DB_UNTIL_G9 = "sqlite3"
CONSTRUCTOR_ALLOWED = False

# mode ∈ {typed, siteblock, listitem, tokens, crm}
SURFACES: dict[str, dict] = {
    "site.settings": {
        "mode": "typed",
        "model": "SiteSettings",
        "note": "singleton pk=1: бренд, контакти, SEO default",
    },
    "site.header": {"mode": "siteblock", "page": "site", "section": "header"},
    "site.footer": {"mode": "siteblock", "page": "site", "section": "footer"},
    "site.theme": {
        "mode": "tokens",
        "note": (
            "лише Unfold-адмінка (вбудований light/dark toggle); "
            "публічний сайт — без теми, дизайн не чіпаємо; "
            "brand COLORS primary #f97f0c у UNFOLD"
        ),
    },
    "home.hero": {
        "mode": "siteblock",
        "page": "home",
        "section": "hero",
        "collection": "HeroSlide",
    },
    "home.audience": {"mode": "siteblock", "page": "home", "section": "audience"},
    "home.categories": {
        "mode": "siteblock",
        "page": "home",
        "section": "categories",
        "list_source": "Category",
    },
    "home.picker": {"mode": "siteblock", "page": "home", "section": "picker"},
    "home.popular": {
        "mode": "siteblock",
        "page": "home",
        "section": "popular",
        "list_source": "Product",
    },
    "home.blog": {
        "mode": "siteblock",
        "page": "home",
        "section": "blog",
        "list_source": "BlogPost",
    },
    "home.district": {"mode": "siteblock", "page": "home", "section": "district"},
    "info.about": {"mode": "siteblock", "page": "about", "section": "body"},
    "info.delivery": {"mode": "siteblock", "page": "delivery", "section": "body"},
    "info.warranty": {"mode": "siteblock", "page": "warranty", "section": "body"},
    "info.returns": {"mode": "siteblock", "page": "returns", "section": "body"},
    "info.install": {"mode": "siteblock", "page": "install", "section": "body"},
    "info.promos": {"mode": "siteblock", "page": "promos", "section": "body"},
    "info.offer": {"mode": "siteblock", "page": "offer", "section": "body"},
    "info.privacy": {"mode": "siteblock", "page": "privacy", "section": "body"},
    "catalog.plp": {"mode": "siteblock", "page": "catalog", "section": "chrome"},
    "catalog.product": {"mode": "listitem", "model": "Product"},
    "catalog.category": {"mode": "listitem", "model": "Category"},
    "catalog.facets": {"mode": "listitem", "model": "Attribute"},
    "blog.post": {"mode": "listitem", "model": "BlogPost"},
    "orders.order": {"mode": "crm", "model": "Order"},
    "orders.quick": {"mode": "crm", "model": "QuickOrder"},
    "leads.contact": {"mode": "crm", "model": "ContactRequest"},
    "leads.callback": {"mode": "crm", "model": "CallbackRequest"},
    "leads.install": {"mode": "crm", "model": "InstallRequest"},
    "leads.photo_pick": {"mode": "crm", "model": "PhotoPickRequest"},
}

# Allowlist винятків hardcode-аудиту (G8)
ALLOWLIST_HARDCODE = (
    "agency credit / PrometeyLabs",
    "aria-label технічні",
    "SVG path geometry",
)

# Waitlist — немає моделі; у сайдбар не додаємо
SKIP_FEATURES = ("waitlist",)

# G6 media
MEDIA = {
    "model": "MediaItem",
    "consumers": ("SiteBlock.media", "HeroSlide.media"),
    "legacy_fields_kept": ("SiteBlock.image", "HeroSlide.image"),
    "note": "Prefer media FK; legacy ImageField kept (additive). WebP on save.",
}

HANDOFF_DOC = "docs/CMS_HANDOFF.md"
PIPELINE_STATUS = {
    "G0": "pass",
    "G1": "pass",
    "G2": "embedded_in_manifest",
    "G3": "pass",
    "G4": "pass_home_header_footer_product",
    "G5": "pass_admin_unfold_theme_only",
    "G6": "pass_mediaitem",
    "G7": "pass_seed_parity",
    "G8": "pass_blockers_0_warns_debt",
    "G9": "pass_handoff_doc",
}
