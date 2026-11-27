"""Дефолти SiteBlock (RU). Порожнє на фронті = fallback на UA."""

from __future__ import annotations

BLOCK_DEFAULTS_RU: dict[tuple[str, str], str] = {
    ("home", "home_seo_title"): "Замки для дверей и мебели — купить в Киеве",
    ("home", "audience_1_title"): "Для дома",
    ("home", "audience_1_text"): "Квартиры, частные дома",
    ("home", "audience_2_title"): "Для бизнеса",
    ("home", "audience_2_text"): "Офисы, магазины, склады",
    ("home", "audience_3_title"): "Для мастеров",
    ("home", "audience_3_text"): "И строительных компаний",
    ("home", "audience_4_title"): "Максимальная безопасность",
    ("home", "audience_4_text"): "Сертифицированная продукция",
    ("home", "picker_title"): "Быстрый подбор замка",
    ("home", "picker_lead"): "Укажите параметры — покажем модели",
    ("home", "picker_step1"): "1. Для каких дверей ищете замок?",
    ("home", "picker_step2"): "2. Уточните параметры",
    ("home", "picker_photo_text"): (
        "Не нашли нужное? Пришлите фото — подберём аналог за 15 минут."
    ),
    ("home", "picker_photo_cta"): "Подбор по фото",
    ("home", "picker_submit"): "Показать модели",
    ("home", "popular_title"): "Популярные товары",
    ("home", "popular_tab_hits"): "Хиты продаж",
    ("home", "popular_tab_news"): "Новинки",
    ("home", "popular_tab_sales"): "Скидки",
    ("home", "blog_title"): "Полезное для выбора",
    ("home", "blog_more_label"): "Полезные статьи о замках",
    ("site", "header_catalog_label"): "Каталог товаров",
    ("site", "header_search_placeholder"): "Поиск замков, цилиндров…",
    ("site", "header_callback_label"): "Перезвоните мне",
    ("site", "header_search_btn"): "Найти",
    ("site", "header_contacts_label"): "Контакты",
    ("site", "header_search_cat"): "Категория",
    ("site", "header_search_brand"): "Бренд",
    ("site", "header_search_product"): "Товар",
    ("site", "header_search_all"): "Показать все результаты",
    ("home", "picker_any"): "Любой",
    ("home", "picker_model_one"): "модель",
    ("home", "picker_model_few"): "модели",
    ("home", "picker_model_many"): "моделей",
    ("home", "picker_for_door"): "Для дверей",
    ("home", "picker_fallback"): "Точных совпадений нет — популярные модели",
    ("home", "picker_recommend"): "Рекомендуем популярные",
    ("home", "picker_picked"): "Подобрали",
    ("home", "picker_none"): "Ничего не найдено",
    ("home", "picker_reset"): "Сбросить",
    ("home", "picker_catalog"): "Перейти в каталог",
    ("home", "picker_empty_title"): "По этим параметрам замков нет",
    ("home", "picker_empty_text"): "Измените параметры или загрузите фото ниже, и мы подберём аналог",
    ("home", "picker_reset_all"): "Сбросить параметры",
    ("home", "picker_stock"): "В наличии",
    ("home", "picker_best"): "Лучшее совпадение",
    ("site", "footer_about_text"): "Замки, цилиндры и фурнитура с доставкой по Киеву.",
    ("site", "footer_catalog_title"): "Каталог",
    ("site", "footer_info_title"): "Информация",
    ("site", "footer_contacts_title"): "Контакты",
    ("site", "footer_copyright"): "© Центр замков",
    ("catalog", "catalog_title"): "Каталог",
    ("catalog", "catalog_empty"): "Товары не найдены",
    ("catalog", "catalog_filters_title"): "Фильтры",
}


def _fill_info_ru_from_map() -> None:
    """RU для інфо-полів: з RU_MAP за UA-дефолтом (якщо є переклад)."""
    from pages.block_defaults import BLOCK_DEFAULTS
    from pages.translations import RU_MAP

    info_pages = {
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
    for (page, key), ua in BLOCK_DEFAULTS.items():
        if page not in info_pages and not (
            page == "site" and key.startswith("info_consult_")
        ):
            continue
        if (page, key) in BLOCK_DEFAULTS_RU:
            continue
        if not ua or key.endswith("_visible"):
            continue
        mapped = RU_MAP.get(ua)
        if mapped:
            BLOCK_DEFAULTS_RU[(page, key)] = mapped


_fill_info_ru_from_map()

from pages.legal_body import default_offer_html, default_privacy_html  # noqa: E402

BLOCK_DEFAULTS_RU[("offer", "offer_body")] = default_offer_html("ru")
BLOCK_DEFAULTS_RU[("privacy", "privacy_body")] = default_privacy_html("ru")
BLOCK_DEFAULTS_RU[("blog", "blog_ask_title")] = "Есть вопросы?"
BLOCK_DEFAULTS_RU[("blog", "blog_ask_text")] = (
    "Консультируем ежедневно по телефону, Viber и Telegram"
)
BLOCK_DEFAULTS_RU[("blog", "blog_ask_cta")] = "Заказать звонок"

from pages.block_defaults_forms import RU as _FORM_RU  # noqa: E402
from pages.block_defaults_shop import RU as _SHOP_RU  # noqa: E402

BLOCK_DEFAULTS_RU.update(_SHOP_RU)
BLOCK_DEFAULTS_RU.update(_FORM_RU)


def get_block_default_ru(page: str, key: str) -> str:
    return BLOCK_DEFAULTS_RU.get((page, key), "")
