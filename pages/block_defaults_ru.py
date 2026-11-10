"""Дефолти SiteBlock (RU). Порожнє на фронті = fallback на UA."""

from __future__ import annotations

BLOCK_DEFAULTS_RU: dict[tuple[str, str], str] = {
    ("home", "audience_1_title"): "Для дома",
    ("home", "audience_1_text"): "Квартиры, частные дома",
    ("home", "audience_2_title"): "Для бизнеса",
    ("home", "audience_2_text"): "Офисы, магазины, склады",
    ("home", "audience_3_title"): "Для мастеров",
    ("home", "audience_3_text"): "И строительных компаний",
    ("home", "audience_4_title"): "Максимальная безопасность",
    ("home", "audience_4_text"): "Сертифицированная продукция",
    ("home", "categories_title"): "Категории",
    ("home", "categories_1_sub"): "Врезные, накладные, электромеханические",
    ("home", "categories_2_sub"): "Секретность и надёжность",
    ("home", "categories_3_sub"): "Ручки, петли, завесы и розетки",
    ("home", "categories_4_sub"): "Защита от взлома",
    ("home", "categories_5_sub"): "Для комфортного закрывания",
    ("home", "categories_6_sub"): "Кодовые замки, домофоны, СКУД",
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
    ("home", "district_others_title"): "Другие районы Киева",
    ("site", "header_catalog_label"): "Каталог",
    ("site", "header_search_placeholder"): "Поиск замков, цилиндров…",
    ("site", "header_callback_label"): "Перезвоните мне",
    ("site", "footer_about_title"): "Центр замков",
    ("site", "footer_about_text"): "Замки, цилиндры и фурнитура с доставкой по Киеву.",
    ("site", "footer_catalog_title"): "Каталог",
    ("site", "footer_info_title"): "Информация",
    ("site", "footer_contacts_title"): "Контакты",
    ("site", "footer_copyright"): "© Центр замков",
    ("catalog", "catalog_title"): "Каталог",
    ("catalog", "catalog_empty"): "Товары не найдены",
    ("catalog", "catalog_filters_title"): "Фильтры",
    ("about", "about_title"): "О нас",
    ("delivery", "delivery_title"): "Доставка и оплата",
    ("warranty", "warranty_title"): "Гарантия",
    ("returns", "returns_title"): "Обмен и возврат",
    ("install", "install_title"): "Установка",
    ("promos", "promos_title"): "Акции",
    ("offer", "offer_title"): "Публичная оферта",
    ("privacy", "privacy_title"): "Политика конфиденциальности",
}


def get_block_default_ru(page: str, key: str) -> str:
    return BLOCK_DEFAULTS_RU.get((page, key), "")
