"""SEO-голова сторінки: title+суфікс, description, canonical/OG/Twitter, verification, JSON-LD.

Правила (узгоджено з SEO-ботом, 2026-11-19):
- canonical = og:url = основний домен + path (без query); порожній домен → не виводимо.
- сторінкові поля (Product.seo_*) мають пріоритет над дефолтами.
- суфікс « | Бренд» не додається, якщо title вже містить бренд.
"""

from __future__ import annotations

import json

from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from pages.i18n_lib import tr

OG_LOCALES = {"ua": "uk_UA", "ru": "ru_RU"}
DEFAULT_TITLE_FALLBACK = "Центр замків"  # колишній хардкод base.html
TITLE_WARN = 60
DESC_MIN, DESC_MAX = 70, 160


def current_lang() -> str:
    code = (get_language() or "ua")[:2].lower()
    return "ru" if code == "ru" else "ua"


def get_seo(request=None):
    from marketing.models import SeoSettings

    if request is not None and hasattr(request, "_marketing_seo"):
        return request._marketing_seo
    try:
        obj = SeoSettings.load()
    except Exception:
        obj = None
    if request is not None:
        request._marketing_seo = obj
    return obj


def get_tracking(request=None):
    from marketing.models import TrackingSettings

    if request is not None and hasattr(request, "_marketing_tracking"):
        return request._marketing_tracking
    try:
        obj = TrackingSettings.load()
    except Exception:
        obj = None
    if request is not None:
        request._marketing_tracking = obj
    return obj


def localized(ua: str, ru: str, lang: str) -> str:
    if lang == "ru":
        if (ru or "").strip():
            return ru.strip()
        return tr((ua or "").strip()) if ua else ""
    return (ua or "").strip()


def default_title(seo, lang: str) -> str:
    if seo is not None:
        value = localized(seo.title_default, seo.title_default_ru, lang)
        if value:
            return value
    return tr(DEFAULT_TITLE_FALLBACK)


def apply_suffix(title: str, suffix: str) -> str:
    suffix = (suffix or "").strip()
    if not suffix or suffix.lower() in title.lower():
        return title
    return f"{title} | {suffix}"


def compose_title(page_title_html: str, seo, lang: str, page_override: str = "") -> str:
    """Повертає безпечний (escaped) title. page_title_html — уже відрендерений блок."""
    if page_override:
        title = conditional_escape(page_override.strip())
    else:
        title = (page_title_html or "").strip()
        if not title:
            title = conditional_escape(default_title(seo, lang))
    suffix = conditional_escape(seo.title_suffix) if seo is not None else ""
    return mark_safe(apply_suffix(str(title), str(suffix)))


def title_length_warning(title: str, suffix: str) -> str:
    full = apply_suffix(title.strip(), suffix)
    if len(full) > TITLE_WARN:
        return f"Title з суфіксом {len(full)} символів (рекомендовано ≤ {TITLE_WARN})."
    return ""


def description_length_warning(desc: str) -> str:
    n = len((desc or "").strip())
    if n and (n < DESC_MIN or n > DESC_MAX):
        return f"Description {n} символів (рекомендовано {DESC_MIN}–{DESC_MAX})."
    return ""


def page_overrides(context, lang: str) -> dict:
    """Сторінкові SEO-поля (зараз — Product.seo_*), мають пріоритет над дефолтами."""
    out = {"title": "", "description": "", "canonical": "", "og_image": None}
    product = context.get("product")
    if product is not None and hasattr(product, "seo_title"):
        out["title"] = localized(product.seo_title, getattr(product, "seo_title_ru", ""), lang)
        out["description"] = localized(
            getattr(product, "seo_description", ""), getattr(product, "seo_description_ru", ""), lang
        )
        out["canonical"] = (getattr(product, "canonical_url", "") or "").strip()
        og = getattr(product, "og_image", None)
        out["og_image"] = og if og else None
    for key in ("title", "description", "canonical"):
        explicit = context.get(f"seo_{key}")
        if explicit:
            out[key] = str(explicit)
    return out


def _abs(domain: str, url: str) -> str:
    if not url:
        return ""
    if url.startswith("https://"):
        return url
    if url.startswith("http://"):
        return ""
    return f"{domain}{url if url.startswith('/') else '/' + url}"


def canonical_for(domain: str, path: str, override: str = "") -> str:
    if override:
        if override.startswith("https://"):
            return override.split("?", 1)[0].split("#", 1)[0]
        if override.startswith("/") and not override.startswith("//"):
            return _abs(domain, override.split("?", 1)[0].split("#", 1)[0])
    return _abs(domain, path)


def _image_info(fieldfile):
    try:
        url = fieldfile.url
    except Exception:
        return None
    w = h = None
    try:
        w, h = fieldfile.width, fieldfile.height
    except Exception:
        pass
    return {"url": url, "width": w, "height": h}


def organization_jsonld(seo, site_settings, domain: str) -> dict | None:
    if not domain:
        return None
    name = (seo.org_name or "").strip() or (getattr(site_settings, "site_name", "") or "").strip()
    if not name:
        return None
    data: dict = {"@context": "https://schema.org", "@type": seo.org_type, "name": name, "url": f"{domain}/"}
    logo = None
    if seo.org_logo:
        logo = _image_info(seo.org_logo)
    elif site_settings is not None and getattr(site_settings, "logo", None):
        info = _image_info(site_settings.logo)
        if info and (info["width"] or 0) >= 112 and (info["height"] or 0) >= 112:
            logo = info
    if logo:
        data["logo"] = _abs(domain, logo["url"])
    same_as = []
    if site_settings is not None:
        for attr in ("instagram_url", "facebook_url", "telegram_url"):
            val = (getattr(site_settings, attr, "") or "").strip()
            if val.startswith("https://"):
                same_as.append(val)
    for line in (seo.same_as or "").splitlines():
        line = line.strip()
        if line.startswith("https://") and line not in same_as:
            same_as.append(line)
    if same_as:
        data["sameAs"] = same_as
    if site_settings is not None:
        from pages.phone import contacts_from_settings

        phone = contacts_from_settings(site_settings).get("tel") or ""
        if phone:
            data["telephone"] = phone
        if (site_settings.email or "").strip():
            data["email"] = site_settings.email.strip()
        if (site_settings.address or "").strip():
            data["address"] = {
                "@type": "PostalAddress",
                "streetAddress": site_settings.address.strip(),
                "addressCountry": "UA",
            }
    return data


def jsonld_script(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    raw = raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{raw}</script>')


def build_head(context) -> dict:
    request = context.get("request")
    lang = current_lang()
    seo = get_seo(request)
    site_settings = context.get("site_settings")
    over = page_overrides(context, lang)
    out = {
        "noindex": bool(seo and seo.global_noindex),
        "description": "",
        "verifications": [],
        "canonical": "",
        "og": None,
        "jsonld": "",
    }
    if seo is None:
        return out
    out["description"] = over["description"] or localized(
        seo.description_default, seo.description_default_ru, lang
    )
    for name, value in (
        ("google-site-verification", seo.google_verification),
        ("msvalidate.01", seo.bing_verification),
        ("facebook-domain-verification", seo.meta_domain_verification),
        ("p:domain_verify", seo.pinterest_verification),
    ):
        if value:
            out["verifications"].append({"name": name, "content": value})
    domain = (seo.primary_domain or "").rstrip("/")
    if not domain or request is None:
        return out
    canonical = canonical_for(domain, request.path, over["canonical"])
    out["canonical"] = canonical
    image = None
    image_alt = ""
    if over["og_image"]:
        image = _image_info(over["og_image"])
        image_alt = ""
    if image is None and seo.og_image:
        image = _image_info(seo.og_image)
        image_alt = seo.og_image_alt
    locale = OG_LOCALES.get(lang, "uk_UA")
    out["og"] = {
        "site_name": (seo.org_name or getattr(site_settings, "site_name", "") or "").strip(),
        "locale": locale,
        "locale_alternates": [v for k, v in OG_LOCALES.items() if v != locale],
        "type": "website",
        "title": context.render_context.get("marketing_title", ""),
        "description": out["description"],
        "url": canonical,
        "image": _abs(domain, image["url"]) if image else "",
        "image_width": image["width"] if image else None,
        "image_height": image["height"] if image else None,
        "image_alt": image_alt if image else "",
        "twitter_card": seo.twitter_card or "summary_large_image",
        "twitter_site": ("@" + seo.twitter_site.lstrip("@")) if seo.twitter_site else "",
    }
    match = getattr(request, "resolver_match", None)
    if match is not None and match.url_name == "home":
        data = organization_jsonld(seo, site_settings, domain)
        if data:
            out["jsonld"] = jsonld_script(data)
    return out
