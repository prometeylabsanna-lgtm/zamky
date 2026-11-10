"""CMS-секції інфосторінок та chrome каталогу."""

from pages.site_content_registry_base import ContentSection, FieldGroup, _b


def _info_body(page: str, title: str, icon: str, preview: str) -> ContentSection:
    return ContentSection(
        slug="body",
        page_slug=page,
        title=title,
        sidebar_icon=icon,
        preview_url=preview,
        visibility_key=f"{page}_section_visible",
        blocks=_b(
            page,
            f"{page}_section_visible",
            f"{page}_title",
            f"{page}_lead",
            f"{page}_body",
            f"{page}_seo_title",
            f"{page}_seo_description",
        ),
        field_groups=(
            FieldGroup("Видимість", (f"{page}_section_visible",)),
            FieldGroup("Контент", (f"{page}_title", f"{page}_lead", f"{page}_body")),
            FieldGroup("SEO", (f"{page}_seo_title", f"{page}_seo_description")),
        ),
    )


CONTENT_SECTIONS_PAGES: tuple[ContentSection, ...] = (
    _info_body("about", "Про нас", "info", "/ua/info/about/"),
    _info_body("delivery", "Доставка і оплата", "local_shipping", "/ua/info/delivery/"),
    _info_body("warranty", "Гарантія", "verified", "/ua/info/warranty/"),
    _info_body("returns", "Обмін та повернення", "swap_horiz", "/ua/info/returns/"),
    _info_body("install", "Установка", "build", "/ua/info/install/"),
    _info_body("promos", "Акції", "local_offer", "/ua/info/promos/"),
    _info_body("offer", "Публічна оферта", "description", "/ua/info/offer/"),
    _info_body("privacy", "Політика конфіденційності", "policy", "/ua/info/privacy/"),
    ContentSection(
        slug="chrome",
        page_slug="catalog",
        title="Каталог — оболонка",
        sidebar_icon="storefront",
        preview_url="/ua/catalog/",
        blocks=_b(
            "catalog",
            "catalog_title",
            "catalog_empty",
            "catalog_filters_title",
        ),
        field_groups=(
            FieldGroup(
                "Тексти",
                ("catalog_title", "catalog_empty", "catalog_filters_title"),
            ),
        ),
    ),
)
