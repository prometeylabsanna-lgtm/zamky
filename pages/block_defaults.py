"""Дефолти SiteBlock (UA) + типи/мітки."""

from __future__ import annotations

BLOCK_LABELS: dict[tuple[str, str], str] = {
    ("home", "hero_section_visible"): "Показувати банер",
    ("home", "audience_section_visible"): "Показувати «Для кого»",
    ("home", "audience_1_title"): "Картка 1 — заголовок",
    ("home", "audience_1_text"): "Картка 1 — текст",
    ("home", "audience_2_title"): "Картка 2 — заголовок",
    ("home", "audience_2_text"): "Картка 2 — текст",
    ("home", "audience_3_title"): "Картка 3 — заголовок",
    ("home", "audience_3_text"): "Картка 3 — текст",
    ("home", "audience_4_title"): "Картка 4 — заголовок",
    ("home", "audience_4_text"): "Картка 4 — текст",
    ("home", "categories_section_visible"): "Показувати категорії",
    ("home", "categories_title"): "Заголовок категорій",
    ("home", "categories_1_sub"): "Підпис категорії 1",
    ("home", "categories_2_sub"): "Підпис категорії 2",
    ("home", "categories_3_sub"): "Підпис категорії 3",
    ("home", "categories_4_sub"): "Підпис категорії 4",
    ("home", "categories_5_sub"): "Підпис категорії 5",
    ("home", "categories_6_sub"): "Підпис категорії 6",
    ("home", "picker_section_visible"): "Показувати підбір",
    ("home", "picker_title"): "Заголовок підбору",
    ("home", "picker_lead"): "Підзаголовок підбору",
    ("home", "picker_step1"): "Крок 1",
    ("home", "picker_step2"): "Крок 2",
    ("home", "picker_photo_text"): "Текст підбору за фото",
    ("home", "picker_photo_cta"): "Кнопка підбору за фото",
    ("home", "picker_submit"): "Кнопка «Показати»",
    ("home", "popular_section_visible"): "Показувати популярні",
    ("home", "popular_title"): "Заголовок популярних",
    ("home", "popular_tab_hits"): "Вкладка «Хіти»",
    ("home", "popular_tab_news"): "Вкладка «Новинки»",
    ("home", "popular_tab_sales"): "Вкладка «Знижки»",
    ("home", "blog_section_visible"): "Показувати блог",
    ("home", "blog_title"): "Заголовок блогу",
    ("home", "blog_more_label"): "Картка «усі статті»",
    ("home", "district_section_visible"): "Показувати блок району",
    ("home", "district_others_title"): "Заголовок інших районів",
    ("site", "header_catalog_label"): "Кнопка каталогу",
    ("site", "header_search_placeholder"): "Плейсхолдер пошуку",
    ("site", "header_callback_label"): "Кнопка «Передзвоніть»",
    ("site", "header_phone_visible"): "Показувати телефон",
    ("site", "header_cart_visible"): "Показувати кошик",
    ("site", "header_wishlist_visible"): "Показувати обране",
    ("site", "footer_about_title"): "Підвал — про нас (заголовок)",
    ("site", "footer_about_text"): "Підвал — про нас (текст)",
    ("site", "footer_catalog_title"): "Підвал — каталог",
    ("site", "footer_info_title"): "Підвал — інфо",
    ("site", "footer_contacts_title"): "Підвал — контакти",
    ("site", "footer_copyright"): "Copyright",
    ("catalog", "catalog_title"): "Заголовок каталогу",
    ("catalog", "catalog_empty"): "Порожній каталог",
    ("catalog", "catalog_filters_title"): "Заголовок фільтрів",
}

BLOCK_DEFAULTS: dict[tuple[str, str], str] = {
    ("home", "hero_section_visible"): "1",
    ("home", "audience_section_visible"): "1",
    ("home", "audience_1_title"): "Для дому",
    ("home", "audience_1_text"): "Квартири, приватні будинки",
    ("home", "audience_2_title"): "Для бізнесу",
    ("home", "audience_2_text"): "Офіси, магазини, склади",
    ("home", "audience_3_title"): "Для майстрів",
    ("home", "audience_3_text"): "Та будівельних компаній",
    ("home", "audience_4_title"): "Максимальна безпека",
    ("home", "audience_4_text"): "Сертифікована продукція",
    ("home", "categories_section_visible"): "1",
    ("home", "categories_title"): "Категорії",
    ("home", "categories_1_sub"): "Врізні, накладні, електромеханічні",
    ("home", "categories_2_sub"): "Секретність та надійність",
    ("home", "categories_3_sub"): "Ручки, петлі, завіси і розетки",
    ("home", "categories_4_sub"): "Захист від злому",
    ("home", "categories_5_sub"): "Для комфортного закривання",
    ("home", "categories_6_sub"): "Кодові замки, домофони, СКУД",
    ("home", "picker_section_visible"): "1",
    ("home", "picker_title"): "Швидкий підбір замка",
    ("home", "picker_lead"): "Вкажіть параметри, ми покажемо моделі",
    ("home", "picker_step1"): "1. Для яких дверей шукаєте замок?",
    ("home", "picker_step2"): "2. Уточніть параметри",
    ("home", "picker_photo_text"): (
        "Не знайшли потрібне? Надішліть фото — підберемо аналог за 15 хвилин."
    ),
    ("home", "picker_photo_cta"): "Підбір за фото",
    ("home", "picker_submit"): "Показати моделі",
    ("home", "popular_section_visible"): "1",
    ("home", "popular_title"): "Популярні товари",
    ("home", "popular_tab_hits"): "Хіти продажу",
    ("home", "popular_tab_news"): "Новинки",
    ("home", "popular_tab_sales"): "Знижки",
    ("home", "blog_section_visible"): "1",
    ("home", "blog_title"): "Корисне для вибору",
    ("home", "blog_more_label"): "Корисні статті про замки",
    ("home", "district_section_visible"): "1",
    ("home", "district_others_title"): "Інші райони Києва",
    ("site", "header_catalog_label"): "Каталог",
    ("site", "header_search_placeholder"): "Пошук замків, циліндрів…",
    ("site", "header_callback_label"): "Передзвоніть мені",
    ("site", "header_phone_visible"): "1",
    ("site", "header_cart_visible"): "1",
    ("site", "header_wishlist_visible"): "1",
    ("site", "footer_about_title"): "Центр замків",
    ("site", "footer_about_text"): "Замки, циліндри та фурнітура з доставкою по Києву.",
    ("site", "footer_catalog_title"): "Каталог",
    ("site", "footer_info_title"): "Інформація",
    ("site", "footer_contacts_title"): "Контакти",
    ("site", "footer_copyright"): "© Центр замків",
    ("catalog", "catalog_title"): "Каталог",
    ("catalog", "catalog_empty"): "Товарів не знайдено",
    ("catalog", "catalog_filters_title"): "Фільтри",
}

INLINE_KEYS: set[tuple[str, str]] = {
    ("home", "audience_1_title"),
    ("home", "audience_2_title"),
    ("home", "audience_3_title"),
    ("home", "audience_4_title"),
    ("home", "categories_title"),
    ("home", "picker_title"),
    ("home", "picker_photo_cta"),
    ("home", "picker_submit"),
    ("home", "popular_title"),
    ("home", "popular_tab_hits"),
    ("home", "popular_tab_news"),
    ("home", "popular_tab_sales"),
    ("home", "blog_title"),
    ("home", "blog_more_label"),
    ("home", "district_others_title"),
    ("site", "header_catalog_label"),
    ("site", "header_search_placeholder"),
    ("site", "header_callback_label"),
    ("site", "footer_about_title"),
    ("site", "footer_catalog_title"),
    ("site", "footer_info_title"),
    ("site", "footer_contacts_title"),
    ("site", "footer_copyright"),
    ("catalog", "catalog_title"),
    ("catalog", "catalog_filters_title"),
}

MULTILINE_KEYS: set[tuple[str, str]] = {
    ("home", "audience_1_text"),
    ("home", "audience_2_text"),
    ("home", "audience_3_text"),
    ("home", "audience_4_text"),
    ("home", "picker_lead"),
    ("home", "picker_photo_text"),
    ("site", "footer_about_text"),
    ("catalog", "catalog_empty"),
}

RICHTEXT_KEYS: set[tuple[str, str]] = set()
STATIC_FALLBACKS: dict[tuple[str, str], str] = {}
IMAGE_KEYS: set[tuple[str, str]] = set()
URL_KEYS: set[tuple[str, str]] = set()

_INFO_PAGES = (
    "about",
    "delivery",
    "warranty",
    "returns",
    "install",
    "promos",
    "offer",
    "privacy",
)
_INFO_TITLES = {
    "about": "Про нас",
    "delivery": "Доставка і оплата",
    "warranty": "Гарантія",
    "returns": "Обмін та повернення",
    "install": "Установка",
    "promos": "Акції",
    "offer": "Публічна оферта",
    "privacy": "Політика конфіденційності",
}

for _page in _INFO_PAGES:
    BLOCK_LABELS[(_page, f"{_page}_section_visible")] = "Показувати сторінку"
    BLOCK_LABELS[(_page, f"{_page}_title")] = "Заголовок"
    BLOCK_LABELS[(_page, f"{_page}_lead")] = "Лід"
    BLOCK_LABELS[(_page, f"{_page}_body")] = "Текст сторінки"
    BLOCK_LABELS[(_page, f"{_page}_seo_title")] = "SEO title"
    BLOCK_LABELS[(_page, f"{_page}_seo_description")] = "SEO description"
    BLOCK_DEFAULTS[(_page, f"{_page}_section_visible")] = "1"
    BLOCK_DEFAULTS[(_page, f"{_page}_title")] = _INFO_TITLES[_page]
    BLOCK_DEFAULTS[(_page, f"{_page}_lead")] = ""
    BLOCK_DEFAULTS[(_page, f"{_page}_body")] = ""
    BLOCK_DEFAULTS[(_page, f"{_page}_seo_title")] = _INFO_TITLES[_page]
    BLOCK_DEFAULTS[(_page, f"{_page}_seo_description")] = ""
    INLINE_KEYS.add((_page, f"{_page}_title"))
    INLINE_KEYS.add((_page, f"{_page}_seo_title"))
    MULTILINE_KEYS.add((_page, f"{_page}_lead"))
    MULTILINE_KEYS.add((_page, f"{_page}_seo_description"))
    RICHTEXT_KEYS.add((_page, f"{_page}_body"))


def get_block_label(page: str, key: str) -> str:
    return BLOCK_LABELS.get((page, key), key)


def get_block_default(page: str, key: str) -> str:
    return BLOCK_DEFAULTS.get((page, key), "1" if key.endswith("_visible") else "")


def get_block_content_type(page: str, key: str) -> str:
    if (page, key) in IMAGE_KEYS or key.endswith("_image"):
        return "image"
    if (page, key) in URL_KEYS or key.endswith("_link") or key.endswith("_url"):
        return "url"
    return "text"


def is_visibility_key(key: str) -> bool:
    return key.endswith("_visible")


def is_richtext_key(page: str, key: str) -> bool:
    return (page, key) in RICHTEXT_KEYS
