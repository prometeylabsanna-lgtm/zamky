"""Дефолти SiteBlock (UA) + типи/мітки."""

from __future__ import annotations

BLOCK_LABELS: dict[tuple[str, str], str] = {
    ("home", "hero_section_visible"): "Показувати банер",
    ("home", "audience_section_visible"): "Показувати «Для кого»",
    ("home", "audience_1_icon"): "Картка 1 — іконка",
    ("home", "audience_1_title"): "Картка 1 — заголовок",
    ("home", "audience_1_text"): "Картка 1 — текст",
    ("home", "audience_2_icon"): "Картка 2 — іконка",
    ("home", "audience_2_title"): "Картка 2 — заголовок",
    ("home", "audience_2_text"): "Картка 2 — текст",
    ("home", "audience_3_icon"): "Картка 3 — іконка",
    ("home", "audience_3_title"): "Картка 3 — заголовок",
    ("home", "audience_3_text"): "Картка 3 — текст",
    ("home", "audience_4_icon"): "Картка 4 — іконка",
    ("home", "audience_4_title"): "Картка 4 — заголовок",
    ("home", "audience_4_text"): "Картка 4 — текст",
    ("home", "categories_section_visible"): "Показувати категорії",
    ("home", "picker_section_visible"): "Показувати підбір",
    ("home", "picker_title"): "Заголовок підбору",
    ("home", "picker_lead"): "Підзаголовок підбору",
    ("home", "picker_step1"): "Крок 1",
    ("home", "picker_step2"): "Крок 2",
    ("home", "picker_photo_text"): "Текст підбору за фото",
    ("home", "picker_photo_cta"): "Кнопка підбору за фото",
    ("home", "picker_submit"): "Кнопка «Показати»",
    ("home", "picker_any"): "Підбір — будь-який",
    ("home", "picker_model_one"): "Підбір — одна модель",
    ("home", "picker_model_few"): "Підбір — кілька моделей",
    ("home", "picker_model_many"): "Підбір — багато моделей",
    ("home", "picker_for_door"): "Підбір — для дверей",
    ("home", "picker_fallback"): "Підбір — немає точних збігів",
    ("home", "picker_recommend"): "Підбір — рекомендуємо",
    ("home", "picker_picked"): "Підбір — підібрали",
    ("home", "picker_none"): "Підбір — нічого не знайдено",
    ("home", "picker_reset"): "Підбір — скинути",
    ("home", "picker_catalog"): "Підбір — у каталог",
    ("home", "picker_empty_title"): "Підбір — порожній заголовок",
    ("home", "picker_empty_text"): "Підбір — порожній текст",
    ("home", "picker_reset_all"): "Підбір — скинути параметри",
    ("home", "picker_stock"): "Підбір — в наявності",
    ("home", "picker_best"): "Підбір — найкращий збіг",
    ("home", "popular_section_visible"): "Показувати популярні",
    ("home", "popular_title"): "Заголовок популярних",
    ("home", "popular_tab_hits"): "Вкладка «Хіти»",
    ("home", "popular_tab_news"): "Заголовок «Новинки»",
    ("home", "popular_tab_sales"): "Вкладка «Знижки»",
    ("home", "blog_section_visible"): "Показувати блог",
    ("home", "blog_title"): "Заголовок блогу",
    ("home", "blog_more_label"): "Картка «усі статті»",
    ("site", "header_catalog_label"): "Кнопка каталогу",
    ("site", "header_search_placeholder"): "Плейсхолдер пошуку",
    ("site", "header_callback_label"): "Кнопка «Передзвоніть»",
    ("site", "header_search_btn"): "Кнопка «Знайти»",
    ("site", "header_contacts_label"): "Підпис «Контакти»",
    ("site", "header_search_cat"): "Пошук — категорія",
    ("site", "header_search_brand"): "Пошук — бренд",
    ("site", "header_search_product"): "Пошук — товар",
    ("site", "header_search_all"): "Пошук — усі результати",
    ("site", "header_phone_visible"): "Показувати телефон",
    ("site", "header_cart_visible"): "Показувати кошик",
    ("site", "header_wishlist_visible"): "Показувати обране",
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
    ("home", "audience_1_icon"): "home",
    ("home", "audience_1_title"): "Для дому",
    ("home", "audience_1_text"): "Квартири, приватні будинки",
    ("home", "audience_2_icon"): "biz",
    ("home", "audience_2_title"): "Для бізнесу",
    ("home", "audience_2_text"): "Офіси, магазини, склади",
    ("home", "audience_3_icon"): "tools",
    ("home", "audience_3_title"): "Для майстрів",
    ("home", "audience_3_text"): "Та будівельних компаній",
    ("home", "audience_4_icon"): "shield",
    ("home", "audience_4_title"): "Максимальна безпека",
    ("home", "audience_4_text"): "Сертифікована продукція",
    ("home", "categories_section_visible"): "1",
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
    ("home", "picker_any"): "Будь-який",
    ("home", "picker_model_one"): "модель",
    ("home", "picker_model_few"): "моделі",
    ("home", "picker_model_many"): "моделей",
    ("home", "picker_for_door"): "Для дверей",
    ("home", "picker_fallback"): "Точних збігів немає — популярні моделі",
    ("home", "picker_recommend"): "Рекомендуємо популярні",
    ("home", "picker_picked"): "Підібрали",
    ("home", "picker_none"): "Нічого не знайдено",
    ("home", "picker_reset"): "Скинути",
    ("home", "picker_catalog"): "Перейти в каталог",
    ("home", "picker_empty_title"): "За цими параметрами замків немає",
    ("home", "picker_empty_text"): "Змініть параметри або завантажте фото нижче, і ми підберемо аналог",
    ("home", "picker_reset_all"): "Скинути параметри",
    ("home", "picker_stock"): "В наявності",
    ("home", "picker_best"): "Найкращий збіг",
    ("home", "popular_section_visible"): "1",
    ("home", "popular_title"): "Популярні товари",
    ("home", "popular_tab_hits"): "Хіти продажу",
    ("home", "popular_tab_news"): "Новинки",
    ("home", "popular_tab_sales"): "Знижки",
    ("home", "blog_section_visible"): "1",
    ("home", "blog_title"): "Корисне для вибору",
    ("home", "blog_more_label"): "Корисні статті про замки",
    ("site", "header_catalog_label"): "Каталог товарів",
    ("site", "header_search_placeholder"): "Пошук замків, циліндрів…",
    ("site", "header_callback_label"): "Передзвоніть мені",
    ("site", "header_search_btn"): "Знайти",
    ("site", "header_contacts_label"): "Контакти",
    ("site", "header_search_cat"): "Категорія",
    ("site", "header_search_brand"): "Бренд",
    ("site", "header_search_product"): "Товар",
    ("site", "header_search_all"): "Показати всі результати",
    ("site", "header_phone_visible"): "1",
    ("site", "header_cart_visible"): "1",
    ("site", "header_wishlist_visible"): "1",
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
    ("home", "picker_title"),
    ("home", "picker_photo_cta"),
    ("home", "picker_submit"),
    ("home", "popular_title"),
    ("home", "popular_tab_hits"),
    ("home", "popular_tab_news"),
    ("home", "popular_tab_sales"),
    ("home", "blog_title"),
    ("home", "blog_more_label"),
    ("site", "header_catalog_label"),
    ("site", "header_search_placeholder"),
    ("site", "header_callback_label"),
    ("site", "header_search_btn"),
    ("site", "header_contacts_label"),
    ("site", "header_search_cat"),
    ("site", "header_search_brand"),
    ("site", "header_search_product"),
    ("site", "header_search_all"),
    ("home", "picker_any"),
    ("home", "picker_model_one"),
    ("home", "picker_model_few"),
    ("home", "picker_model_many"),
    ("home", "picker_for_door"),
    ("home", "picker_recommend"),
    ("home", "picker_picked"),
    ("home", "picker_none"),
    ("home", "picker_reset"),
    ("home", "picker_catalog"),
    ("home", "picker_empty_title"),
    ("home", "picker_reset_all"),
    ("home", "picker_stock"),
    ("home", "picker_best"),
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
    ("home", "picker_fallback"),
    ("home", "picker_empty_text"),
    ("site", "footer_about_text"),
    ("catalog", "catalog_empty"),
}

RICHTEXT_KEYS: set[tuple[str, str]] = set()
from pages.audience_icons import AUDIENCE_ICON_STATICS  # noqa: E402

STATIC_FALLBACKS: dict[tuple[str, str], str] = {
    ("home", f"audience_{i}_icon"): path
    for i, path in enumerate(AUDIENCE_ICON_STATICS, start=1)
}
IMAGE_KEYS: set[tuple[str, str]] = set()
URL_KEYS: set[tuple[str, str]] = set()

# Інфосторінки: структуровані поля (картки / таблиці / кроки).
from pages import block_defaults_info_1 as _info1  # noqa: E402
from pages import block_defaults_info_2 as _info2  # noqa: E402,F401
from pages import block_defaults_forms as _forms  # noqa: E402
from pages import block_defaults_shop as _shop  # noqa: E402

BLOCK_LABELS.update(_info1.LABELS)
BLOCK_LABELS.update(_shop.LABELS)
BLOCK_LABELS.update(_forms.LABELS)
BLOCK_DEFAULTS.update(_info1.DEFAULTS)
BLOCK_DEFAULTS.update(_shop.DEFAULTS)
BLOCK_DEFAULTS.update(_forms.DEFAULTS)
INLINE_KEYS.update(_info1.INLINE)
INLINE_KEYS.update(_forms.INLINE)
MULTILINE_KEYS.update(_info1.MULTILINE)
MULTILINE_KEYS.update(_shop.MULTILINE)
MULTILINE_KEYS.update(_forms.MULTILINE)
RICHTEXT_KEYS.update(_info1.RICHTEXT)


def get_block_label(page: str, key: str) -> str:
    return BLOCK_LABELS.get((page, key), key)


def get_block_default(page: str, key: str) -> str:
    return BLOCK_DEFAULTS.get((page, key), "1" if key.endswith("_visible") else "")


def get_block_content_type(page: str, key: str) -> str:
    if (
        (page, key) in IMAGE_KEYS
        or key.endswith("_image")
        or key.endswith("_icon")
    ):
        return "image"
    if (page, key) in URL_KEYS or key.endswith("_link") or key.endswith("_url"):
        return "url"
    return "text"


def is_visibility_key(key: str) -> bool:
    return key.endswith("_visible")


def is_richtext_key(page: str, key: str) -> bool:
    return (page, key) in RICHTEXT_KEYS
