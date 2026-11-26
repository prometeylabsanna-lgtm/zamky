"""Registry CMS-секцій → sidebar + proxy admin."""

from __future__ import annotations

from typing import Iterable

from pages.site_content_registry_base import ContentSection
from pages.site_content_registry_home import CONTENT_SECTIONS_HOME
from pages.site_content_registry_pages import CONTENT_SECTIONS_PAGES
from pages.site_content_registry_pages_2 import CONTENT_SECTIONS_PAGES_2

CONTENT_SECTIONS: tuple[ContentSection, ...] = (
    CONTENT_SECTIONS_HOME + CONTENT_SECTIONS_PAGES + CONTENT_SECTIONS_PAGES_2
)

_SIDEBAR_GROUPS: tuple[tuple[str, frozenset[str]], ...] = (
    ("Оболонка сайту", frozenset({"site"})),
    ("Головна", frozenset({"home"})),
    ("Підбір", frozenset()),
    (
        "Інфосторінки",
        frozenset(
            {
                "about",
                "delivery",
                "warranty",
                "returns",
                "install",
                "promos",
                "offer",
                "privacy",
                "blog",
            }
        ),
    ),
    ("Каталог (CMS)", frozenset({"catalog", "product"})),
)

_TITLE_PREFIXES = (
    "Головна — ",
)


def get_section(page_slug: str, section_slug: str) -> ContentSection | None:
    for section in CONTENT_SECTIONS:
        if section.page_slug == page_slug and section.slug == section_slug:
            return section
    return None


def all_registry_block_keys() -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for section in CONTENT_SECTIONS:
        for pair in section.blocks:
            if pair not in seen:
                seen.add(pair)
                keys.append(pair)
    return keys


def _sidebar_item_title(section: ContentSection) -> str:
    title = section.sidebar_title or section.title
    for prefix in _TITLE_PREFIXES:
        if title.startswith(prefix):
            return title[len(prefix) :]
    return title


def _section_group_title(section: ContentSection) -> str:
    if section.sidebar_group:
        return section.sidebar_group
    for group_title, page_slugs in _SIDEBAR_GROUPS:
        if section.page_slug in page_slugs:
            return group_title
    return "Інше"


def blog_parent_nav_active(request) -> bool:
    path = (getattr(request, "path", "") or "").lower()
    return (
        "blogbodysettings" in path
        or "blogasksettings" in path
        or "blogpost" in path
    )


def _blog_nested_items(admin_prefix: str) -> list[dict]:
    prefix = admin_prefix.strip("/")
    return [
        {
            "title": "Список статей",
            "icon": "article",
            "link": f"/{prefix}/pages/blogpost/",
        },
        {
            "title": "Маєте питання?",
            "icon": "support_agent",
            "link": f"/{prefix}/pages/blogasksettings/",
        },
    ]


def _section_to_item(section: ContentSection, admin_prefix: str = "admin/") -> dict:
    # Рядок, не reverse: Unfold бере link як готовий шлях.
    prefix = admin_prefix.strip("/")
    item = {
        "title": _sidebar_item_title(section),
        "icon": section.sidebar_icon,
        "link": f"/{prefix}/pages/{section.admin_model_name}/",
    }
    if section.page_slug == "blog" and section.slug == "body":
        item["active"] = "pages.site_content_registry.blog_parent_nav_active"
        item["items"] = _blog_nested_items(admin_prefix)
    return item


def build_content_sidebar_groups(admin_prefix: str = "admin/") -> list[dict]:
    buckets: dict[str, list[dict]] = {title: [] for title, _ in _SIDEBAR_GROUPS}
    buckets["Інше"] = []

    for section in CONTENT_SECTIONS:
        if section.hide_from_sidebar:
            continue
        buckets[_section_group_title(section)].append(
            _section_to_item(section, admin_prefix)
        )

    groups: list[dict] = []
    first = True
    for title, _ in _SIDEBAR_GROUPS:
        items = buckets[title]
        if not items:
            continue
        groups.append(
            {
                "title": title,
                "separator": first,
                "collapsible": True,
                "items": items,
            }
        )
        first = False

    if buckets["Інше"]:
        groups.append(
            {
                "title": "Інше",
                "separator": first,
                "collapsible": True,
                "items": buckets["Інше"],
            }
        )
    return groups


def iter_section_blocks(section: ContentSection) -> Iterable[tuple[str, str]]:
    return section.blocks
