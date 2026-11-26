"""Підказки для CMS-форм: тексти, межі символів, фото."""

SECTION_HINTS: dict[tuple[str, str], str] = {
    ("home", "hero"): "Слайди банера: фото, підпис і кнопки. Порядок — перетягніть у списку.",
    ("home", "audience"): (
        "Чотири картки «для кого»: іконка, заголовок і підтекст. "
        "Іконка однакова для української та російської. Новий файл замінить поточну."
    ),
    ("home", "categories"): (
        "Картки — реальні категорії. Клік відкриває фото, назву і підпис. "
        "«Додати» ставить картку в кінець стрічки на сайті."
    ),
    ("home", "picker"): "Заголовок, кроки і кнопки підбору. Мови — вкладки зверху.",
    ("home", "picker_doors"): (
        "Картки дверей: фото, підпис і категорії товарів. "
        "Підбір покаже товари з обраних категорій. Мови — вкладки зверху."
    ),
    ("home", "picker_filters"): (
        "Новий фільтр береться з фільтра каталогу — варіанти підтягнуться самі. "
        "Можна додати або видалити варіант. Мови — вкладки зверху."
    ),
    ("home", "picker_style"): "Кольори блоку підбору на головній.",
    ("home", "popular"): (
        "Товари на головній у вкладках Хіти / Новинки / Знижки. "
        "Порядок зверху вниз — як на сайті."
    ),
    ("site", "header"): (
        "Підписи шапки, видимість іконок і ряд кнопок під пошуком. "
        "Мови — вкладки зверху."
    ),
    ("site", "footer"): (
        "Тексти підвалу та списки посилань: каталог, інформація, юридичні, дзвінок. "
        "Мови — вкладки зверху."
    ),
    ("about", "form"): (
        "Заголовок, поля, теми й кнопка форми внизу інфосторінок. "
        "Змінюйте лише підписи тем — у заявках лишаються ті самі теми. "
        "Телефон біля кнопки — з «Контакти та бренд»."
    ),
    ("offer", "body"): (
        "Один редактор: заголовки, абзаци, списки, блок реквізитів (цитата). "
        "Мови — вкладки зверху."
    ),
    ("privacy", "body"): (
        "Один редактор: заголовки, абзаци, список, жовта виноска. "
        "Мови — вкладки зверху."
    ),
    ("blog", "body"): (
        "Шапка списку статей. Самі тексти — підменю «Список статей». "
        "Чорна картка — «Маєте питання?»."
    ),
    ("blog", "ask"): (
        "Чорна картка справа: заголовок, текст, телефон, графік і кнопка. "
        "Кнопка відкриває форму «Замовити дзвінок». Мови — вкладки зверху."
    ),
    ("catalog", "chrome"): (
        "Заголовок загального каталогу, порожній стан і підпис «Фільтри» "
        "(кнопка й панель лише на телефоні та планшеті). "
        "На сторінці категорії заголовок лишається назвою категорії."
    ),
}

KEY_HINTS: dict[str, str] = {
    "footer_copyright": "Рік можна оновлювати вручну.",
    "blog_more_label": (
        "На картках блогу на головній, лише якщо немає жодної опублікованої статті. "
        "Якщо статті є — на картках їхні назви."
    ),
    "about_form_or_call": (
        "Текст перед телефоном. Номер — з Налаштування → Контакти та бренд."
    ),
    "about_form_topic_lock": "Підпис у списку «Тема» на формі. У заявці тема не зміниться.",
    "about_form_err_required": "Показ, якщо клієнт лишив поле порожнім.",
    "offer_body": "Заголовок у редакторі стає підзаголовком на сайті. Цитата — сірий блок реквізитів.",
    "privacy_body": "Маркований список як на сайті. Окремий абзац-виноска буде жовтим блоком.",
    "blog_ask_cta": "Підпис кнопки. Клік відкриває вікно «Замовити дзвінок».",
    "catalog_filters_title": (
        "Кнопка і заголовок панелі фільтрів на телефоні та планшеті. "
        "На великому екрані не показується."
    ),
}

IMAGE_HINTS: dict[str, str] = {
    "audience_icon": (
        "Іконка зліва на картці. PNG, SVG або WebP, бажано квадрат до 200 px."
    ),
    "hero": "Широке фото ~1920×900 (кадр близько 2:1), до 3 МБ. Файл сам стане легшим.",
    "logo": "Логотип у шапці. Краще з прозорим фоном, до 3 МБ.",
    "favicon": "Маленька іконка вкладки браузера. Квадрат 32–256 px; .ico лишиться як є.",
    "category": "Квадратне фото або лого 400–800 px, до 3 МБ. Порожнє — стандартне.",
    "product": "Фото товару, довша сторона від ~800 px, до 3 МБ. Файл сам стане легшим.",
    "og": "Картинка при поширенні в соцмережах, бажано 1200×630 px, до 3 МБ.",
    "blog": "Обкладинка на картці та сторінці статті, бажано 1200×630 px, до 3 МБ.",
    "picker_door": "Фото дверей. Порожнє — стандартне. Краще горизонтальне, до 3 МБ.",
}

SECTION_VISIBLE_HINT = "Без галочки цей блок не показується на сайті."
SEO_TITLE_HINT = (
    "Заголовок вкладки браузера. Порожнє — загальний з SEO-налаштувань."
)
SEO_DESC_HINT = (
    "Короткий опис для пошуку. Порожнє — загальний з SEO-налаштувань."
)
URL_HINT = (
    "Шлях на сайті (/catalog/), якір (#picker) або повне посилання з https://."
)
STYLE_HINT = "Колір цього блоку на сайті. Скидання — як зараз на вітрині."
RU_HINT = "Порожнє = український текст на вітрині."

# Рекомендовані межі за версткою (лічильник не блокує збереження).
CHAR_BY_KEY: dict[str, dict] = {
    "picker_title": {"max": 60},
    "picker_lead": {"max": 110},
    "picker_photo_cta": {"max": 28},
    "picker_submit": {"max": 28},
    "popular_title": {"max": 60},
    "blog_title": {"max": 60},
    "blog_more_label": {"max": 28},
    "catalog_title": {"max": 60},
    "catalog_filters_title": {"max": 28},
    "header_catalog_label": {"max": 28},
    "header_callback_label": {"max": 28},
    "header_search_placeholder": {"max": 40},
}

CHAR_BY_FIELD: dict[str, dict] = {
    "name": {"max": 80},
    "title": {"max": 70},
    "excerpt": {"max": 140},
    "home_subtitle": {"max": 40},
    "headline": {"max": 60},
    "subtitle": {"max": 110},
    "cta_primary_label": {"max": 28},
    "cta_secondary_label": {"max": 28},
    "seo_title": {"max": 60},
    "seo_description": {"min": 70, "max": 160},
    "title_default": {"max": 60, "suffix": True},
    "description_default": {"min": 70, "max": 160},
    "og_image_alt": {"max": 125},
    "h1": {"max": 70},
}


def help_for_section(page: str, slug: str) -> str:
    return SECTION_HINTS.get((page, slug), "")


def help_for_key(key: str, page: str = "") -> str:
    del page
    if key.startswith("audience_") and key.endswith("_icon"):
        return IMAGE_HINTS["audience_icon"]
    if key.endswith("_seo_title"):
        return SEO_TITLE_HINT
    if key.endswith("_seo_description"):
        return SEO_DESC_HINT
    return KEY_HINTS.get(key, "")


def char_rule_for_key(key: str) -> dict | None:
    if key in CHAR_BY_KEY:
        return CHAR_BY_KEY[key]
    if key.endswith("_seo_title"):
        return {"max": 60}
    if key.endswith("_seo_description"):
        return {"min": 70, "max": 160}
    if key.endswith(("_cta", "_label", "_submit")):
        return {"max": 28}
    if key.startswith("audience_") and key.endswith("_title"):
        return {"max": 28}
    if key.startswith("audience_") and key.endswith("_text"):
        return {"max": 40}
    if key.endswith("_title") or key.endswith("_headline"):
        return {"max": 60}
    if key.endswith("_lead") or key.endswith("_subtitle"):
        return {"max": 110}
    return None


def char_rule_for_field(name: str) -> dict | None:
    if name in CHAR_BY_FIELD:
        return CHAR_BY_FIELD[name]
    if name.endswith('_ru'):
        return CHAR_BY_FIELD.get(name[:-3])
    if name.endswith('_default_ru'):
        return CHAR_BY_FIELD.get(name.replace('_ru', ''))
    return None


def apply_form_char_hints(form, names=None) -> None:
    fields = getattr(form, 'fields', None) or getattr(form, 'base_fields', {})
    for name in names or list(fields):
        apply_char_hint(fields.get(name), char_rule_for_field(name))


def apply_char_hint(field, rule: dict | None) -> None:
    if field is None or not rule:
        return
    attrs = getattr(field.widget, "attrs", None)
    if attrs is None:
        return
    if rule.get("max"):
        attrs["data-char-max"] = str(rule["max"])
    if rule.get("min"):
        attrs["data-char-min"] = str(rule["min"])
    if rule.get("suffix"):
        attrs["data-char-suffix"] = "1"
