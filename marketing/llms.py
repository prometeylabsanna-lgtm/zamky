"""Текст /llms.txt лише з фактів CMS і каталогу."""

from __future__ import annotations

from django.urls import reverse
from django.utils.translation import override

from catalog.models import Category
from marketing.feeds import resolve_base_url
from pages.hero_slides import get_hero_slides
from pages.info_cms import is_info_page_visible
from pages.models_cms import SiteSettings
from pages.models_extra import BlogPost
from pages.views import INFO_NAV, INFO_PAGES

HOME_H1_FALLBACK = "Замки для дверей та меблів — купити в Києві"


def _abs(base: str, path: str) -> str:
    if not path:
        return base
    if path.startswith("https://"):
        return path
    return f"{base}{path if path.startswith('/') else '/' + path}"


def _name(settings) -> str:
    value = (getattr(settings, "site_name", "") or "").strip()
    return value or "Центр замків"


def _home_h1() -> str:
    slides = get_hero_slides("ua")
    if not slides:
        return HOME_H1_FALLBACK
    parts = [slides[0].headline or "", slides[0].headline_accent or ""]
    text = " ".join(p for p in parts if p).strip()
    return text or HOME_H1_FALLBACK


def _contacts(settings) -> list[str]:
    lines = []
    phone = (getattr(settings, "phone", "") or "").strip()
    email = (getattr(settings, "email", "") or "").strip()
    address = (getattr(settings, "address", "") or "").strip()
    hours = (getattr(settings, "work_hours", "") or "").strip()
    if phone:
        lines.append(f"- Телефон: {phone}")
    if email:
        lines.append(f"- Email: {email}")
    if address:
        lines.append(f"- Адреса: {address}")
    if hours:
        lines.append(f"- Графік: {hours}")
    for attr, label in (
        ("instagram_url", "Instagram"),
        ("facebook_url", "Facebook"),
        ("telegram_url", "Telegram"),
    ):
        url = (getattr(settings, attr, "") or "").strip()
        if url.startswith("https://"):
            lines.append(f"- {label}: {url}")
    return lines


def build_llms_txt(request=None) -> str:
    settings = SiteSettings.load()
    base = resolve_base_url(request)
    with override("ua"):
        home = reverse("catalog:home")
        catalog = reverse("catalog:catalog")
        info_links = []
        for key in INFO_NAV:
            if not is_info_page_visible(key):
                continue
            if key == "blog":
                path = reverse("pages:blog_list")
            else:
                path = reverse("pages:info_page", kwargs={"page": key})
            info_links.append((INFO_PAGES[key]["name"], path))
        categories = [
            (cat.name, cat.get_absolute_url())
            for cat in Category.objects.filter(is_active=True).order_by("sort_order", "name")
        ]
        posts = [
            (post.title, post.get_absolute_url())
            for post in BlogPost.objects.filter(is_published=True).order_by(
                "sort_order", "-created_at"
            )
        ]

    name = _name(settings)
    lines = [
        f"# {name}",
        "",
        f"> {_home_h1()}",
        "",
        "## Розділи",
        f"- [Головна]({_abs(base, home)})",
        f"- [Каталог]({_abs(base, catalog)})",
    ]
    for title, path in info_links:
        lines.append(f"- [{title}]({_abs(base, path)})")
    if categories:
        lines += ["", "## Категорії"]
        for title, path in categories:
            lines.append(f"- [{title}]({_abs(base, path)})")
    if posts:
        lines += ["", "## Статті"]
        for title, path in posts:
            lines.append(f"- [{title}]({_abs(base, path)})")
    contacts = _contacts(settings)
    if contacts:
        lines += ["", "## Контакти"]
        lines += contacts
    lines.append("")
    return "\n".join(lines)
