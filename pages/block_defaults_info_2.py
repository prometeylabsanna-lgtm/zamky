"""Інфо CMS: install, promos, offer, privacy, blog, consult — labels + UA defaults."""

from __future__ import annotations

from pages.block_defaults_info_1 import (
    DEFAULTS,
    INLINE,
    LABELS,
    MULTILINE,
    RICHTEXT,
    _common_head,
    _reg,
)
from pages.legal_body import default_offer_html, default_privacy_html

# --- install ---
_common_head(
    "install",
    "Установка замків",
    "Встановлюємо замки, циліндри, броненакладки та дотягувачі в Києві та області. "
    "Виїзд у зручний час, гарантія на роботи 12 місяців.",
)
_reg("install", "install_card_1_value", "Картка 1 — значення", "від 30 хв", kind="inline")
_reg("install", "install_card_1_title", "Картка 1 — заголовок", "Досвідчені майстри", kind="inline")
_reg(
    "install",
    "install_card_1_text",
    "Картка 1 — текст",
    "Швидко та акуратно, без пошкодження дверей",
)
_reg("install", "install_card_2_value", "Картка 2 — значення", "12 міс.", kind="inline")
_reg("install", "install_card_2_title", "Картка 2 — заголовок", "Гарантія на роботи", kind="inline")
_reg("install", "install_card_2_text", "Картка 2 — текст", "Безкоштовно усуваємо недоліки монтажу")
_reg("install", "install_card_3_value", "Картка 3 — значення", "24/7", kind="inline")
_reg("install", "install_card_3_title", "Картка 3 — заголовок", "Виїзд у зручний час", kind="inline")
_reg("install", "install_card_3_text", "Картка 3 — текст", "Також аварійне відкриття дверей")
_reg("install", "install_prices_title", "Ціни — заголовок", "Ціни на послуги", kind="inline")
_PRICE_ROWS = (
    ("Заміна циліндра", "від 400 ₴"),
    ("Врізання замка в металеві двері", "від 1200 ₴"),
    ("Врізання замка в міжкімнатні двері", "від 600 ₴"),
    ("Встановлення броненакладки", "від 500 ₴"),
    ("Встановлення дотягувача", "від 500 ₴"),
    ("Монтаж кодового замка", "від 900 ₴"),
    ("Аварійне відкриття дверей", "від 800 ₴"),
)
for i, (lab, val) in enumerate(_PRICE_ROWS, start=1):
    _reg("install", f"install_price_{i}_label", f"Ціна {i} — послуга", lab, kind="inline")
    _reg("install", f"install_price_{i}_value", f"Ціна {i} — сума", val, kind="inline")
_reg("install", "install_steps_title", "Кроки — заголовок", "Як ми працюємо", kind="inline")
_reg("install", "install_step_1_title", "Крок 1 — заголовок", "Заявка", kind="inline")
_reg("install", "install_step_1_text", "Крок 1 — текст", "Телефоном або через форму на сайті")
_reg("install", "install_step_2_title", "Крок 2 — заголовок", "Узгодження", kind="inline")
_reg("install", "install_step_2_text", "Крок 2 — текст", "Підбираємо замок і час виїзду")
_reg("install", "install_step_3_title", "Крок 3 — заголовок", "Виїзд майстра", kind="inline")
_reg("install", "install_step_3_text", "Крок 3 — текст", "Привозимо все необхідне")
_reg("install", "install_step_4_title", "Крок 4 — заголовок", "Встановлення", kind="inline")
_reg("install", "install_step_4_text", "Крок 4 — текст", "Перевірка роботи та гарантія")
_reg("install", "install_form_title", "Форма — заголовок", "Замовити установку", kind="inline")

# --- promos ---
_common_head(
    "promos",
    "Акції та спецпропозиції",
    "Знижки на замки, циліндри та комплекти з установкою. Пропозиції оновлюються щомісяця.",
)
_PROMOS = (
    ("-20%", "Циліндри зі знижкою до 20%", "Ключ-ключ та ключ-вертушка провідних брендів", "До 31.10.2026"),
    ("-15%", "Замок + установка", "Знижка 15% на встановлення при купівлі замка", "До 30.11.2026"),
    ("Подарунок", "Броненакладка в подарунок", "При замовленні замка підвищеного захисту", "До 31.10.2026"),
    ("-10%", "Кодові замки", "Знижка 10% на кодові та біометричні замки", "До 15.11.2026"),
)
for i, (badge, title, text, until) in enumerate(_PROMOS, start=1):
    _reg("promos", f"promos_item_{i}_badge", f"Акція {i} — плашка", badge, kind="inline")
    _reg("promos", f"promos_item_{i}_title", f"Акція {i} — заголовок", title, kind="inline")
    _reg("promos", f"promos_item_{i}_text", f"Акція {i} — текст", text)
    _reg("promos", f"promos_item_{i}_until", f"Акція {i} — термін", until, kind="inline")
_reg("promos", "promos_terms_title", "Умови — заголовок", "Умови акцій", kind="inline")
_reg("promos", "promos_terms_1", "Умова 1", "Знижки за різними акціями не сумуються")
_reg("promos", "promos_terms_2", "Умова 2", "Кількість товару за акційною ціною обмежена")
_reg("promos", "promos_terms_3", "Умова 3", "Деталі уточнюйте у менеджера")

# --- offer ---
_common_head(
    "offer",
    "Публічна оферта",
    "Цей документ є публічною пропозицією (офертою) [ПІБ ФОП], РНОКПП [номер] (далі — Продавець), "
    "укласти договір купівлі-продажу товарів дистанційним способом з будь-якою фізичною або "
    "юридичною особою (далі — Покупець).",
)
_reg("offer", "offer_rev", "Редакція", "Редакція від 6 жовтня 2026 року", kind="inline")
_reg(
    "offer",
    "offer_body",
    "Текст сторінки",
    default_offer_html("ua"),
    kind="richtext",
)

# --- privacy ---
_common_head(
    "privacy",
    "Політика конфіденційності",
    "Ця політика пояснює, які персональні дані ми збираємо, навіщо вони потрібні та як ми їх захищаємо. "
    "Користуючись сайтом, ви погоджуєтеся з її умовами.",
)
_reg("privacy", "privacy_rev", "Редакція", "Редакція від 6 жовтня 2026 року", kind="inline")
_reg(
    "privacy",
    "privacy_body",
    "Текст сторінки",
    default_privacy_html("ua"),
    kind="richtext",
)

# --- blog list chrome ---
_common_head(
    "blog",
    "Корисне для вибору",
    "Поради з вибору, встановлення та догляду за замками й фурнітурою.",
)
_reg("blog", "blog_ask_visible", "Показувати картку", "1", kind="inline")
_reg("blog", "blog_ask_title", "Заголовок", "Маєте питання?", kind="inline")
_reg(
    "blog",
    "blog_ask_text",
    "Текст",
    "Консультуємо щодня в телефоні, Viber та Telegram",
)
_reg("blog", "blog_ask_phone", "Телефон", "", kind="inline")
_reg("blog", "blog_ask_hours", "Графік", "", kind="inline")
_reg("blog", "blog_ask_cta", "Текст кнопки", "Замовити дзвінок", kind="inline")

# --- shared consult (site) ---
_reg(
    "site",
    "info_consult_hint",
    "Підпис",
    "Потрібна консультація?",
    kind="inline",
)
_reg("site", "info_consult_phone", "Телефон", "", kind="inline")
_reg("site", "info_consult_hours", "Графік", "", kind="inline")
_reg(
    "site",
    "info_consult_cta",
    "Текст кнопки",
    "Написати нам",
    kind="inline",
)

# --- errors ---
_reg("errors", "err404_title", "404 — заголовок", "Сторінку не знайдено", kind="inline")
_reg(
    "errors",
    "err404_text",
    "404 — текст",
    "Можливо, її видалили або адресу введено з помилкою. "
    "Спробуйте пошук або перейдіть до каталогу.",
)
_reg("errors", "err403_title", "403 — заголовок", "Доступ заборонено", kind="inline")
_reg(
    "errors",
    "err403_text",
    "403 — текст",
    "Сторінка недоступна. Якщо ви заповнювали форму — оновіть сторінку і спробуйте ще раз.",
)
_reg("errors", "err_home_btn", "Кнопка «На головну»", "На головну", kind="inline")
_reg("errors", "err_catalog_btn", "Кнопка «До каталогу»", "До каталогу", kind="inline")

# quiet linters for unused richtext set (kept for merge API)
assert RICHTEXT is not None
assert LABELS and DEFAULTS and INLINE and MULTILINE
