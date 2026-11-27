"""Тексти успіху форм: ключі SiteBlock."""

from __future__ import annotations

LABELS: dict[tuple[str, str], str] = {
    ("about", "about_form_done_title"): "Після відправки — заголовок",
    ("about", "about_form_done_text"): "Після відправки — текст",
    ("about", "about_form_done_again"): "Кнопка «надіслати ще»",
    ("install", "install_submit"): "Кнопка форми",
    ("install", "install_done_title"): "Після заявки — заголовок",
    ("install", "install_done_text"): "Після заявки — текст",
    ("site", "cb_done_title"): "Після відправки — заголовок",
    ("site", "cb_done_text"): "Після відправки — текст",
    ("site", "photo_sent_title"): "Після відправки — заголовок",
    ("site", "photo_sent_text"): "Після відправки — текст",
    ("product", "quick_done"): "Після швидкого замовлення",
}

DEFAULTS: dict[tuple[str, str], str] = {
    ("about", "about_form_done_title"): "Дякуємо, {name}!",
    ("about", "about_form_done_text"): 'Ваше повідомлення отримано. Менеджер зв’яжеться з вами за номером {phone} протягом робочого дня.',
    ("about", "about_form_done_again"): "Надіслати ще одне повідомлення",
    ("install", "install_submit"): "Замовити установку",
    ("install", "install_done_title"): "Заявку прийнято!",
    ("install", "install_done_text"): 'Менеджер звʼяжеться з вами за номером {phone}, щоб узгодити час виїзду.',
    ("site", "cb_done_title"): "Дякуємо!",
    ("site", "cb_done_text"): 'Менеджер передзвонить вам на номер {phone} протягом 15 хвилин.',
    ("site", "photo_sent_title"): "Фото надіслано!",
    ("site", "photo_sent_text"): "Майстер перегляне фото і надішле варіанти протягом 15 хвилин.",
    ("product", "quick_done"): "Дякуємо! Ми скоро передзвонимо",
}

RU: dict[tuple[str, str], str] = {
    ("about", "about_form_done_title"): "Спасибо, {name}!",
    ("about", "about_form_done_text"): "Ваше сообщение получено. Менеджер свяжется с вами по номеру {phone} в течение рабочего дня.",
    ("about", "about_form_done_again"): "Отправить ещё одно сообщение",
    ("install", "install_submit"): "Заказать установку",
    ("install", "install_done_title"): "Заявка принята!",
    ("install", "install_done_text"): "Менеджер свяжется с вами по номеру {phone}, чтобы согласовать время выезда.",
    ("site", "cb_done_title"): "Спасибо!",
    ("site", "cb_done_text"): "Менеджер перезвонит вам на номер {phone} в течение 15 минут.",
    ("site", "photo_sent_title"): "Фото отправлено!",
    ("site", "photo_sent_text"): "Мастер посмотрит фото и пришлёт варианты в течение 15 минут.",
    ("product", "quick_done"): "Спасибо! Мы скоро перезвоним",
}

INLINE: set[tuple[str, str]] = {
    ("about", "about_form_done_title"),
    ("about", "about_form_done_again"),
    ("install", "install_submit"),
    ("install", "install_done_title"),
    ("site", "cb_done_title"),
    ("site", "photo_sent_title"),
    ("product", "quick_done"),
}

MULTILINE: set[tuple[str, str]] = {
    ("about", "about_form_done_text"),
    ("install", "install_done_text"),
    ("site", "cb_done_text"),
    ("site", "photo_sent_text"),
}
