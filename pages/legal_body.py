"""HTML-тіло юридичних сторінок (оферта, політика) + санітизація."""

from __future__ import annotations

import re
from html import escape

from django.utils.html import linebreaks
from lxml import html as lhtml

from pages.translations import RU_MAP

ALLOWED_TAGS = frozenset(
    {
        "p",
        "h2",
        "h3",
        "ul",
        "ol",
        "li",
        "a",
        "strong",
        "em",
        "b",
        "i",
        "u",
        "br",
        "blockquote",
        "div",
    }
)
ALLOWED_ATTR = {
    "a": frozenset({"href", "title", "rel", "target"}),
    "p": frozenset({"class"}),
    "h2": frozenset({"class"}),
    "blockquote": frozenset({"class"}),
    "div": frozenset({"class"}),
}

OFFER_INTRO = (
    "Цей документ є публічною пропозицією (офертою) [ПІБ ФОП], РНОКПП [номер] "
    "(далі — Продавець), укласти договір купівлі-продажу товарів дистанційним "
    "способом з будь-якою фізичною або юридичною особою (далі — Покупець)."
)
OFFER_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "1. Загальні положення",
        (
            "1.1. Оформлення замовлення на сайті означає повне й беззастережне прийняття Покупцем умов цього договору.",
            "1.2. Продавець має право змінювати умови оферти. Нова редакція набирає чинності з моменту публікації на сайті.",
        ),
    ),
    (
        "2. Предмет договору",
        (
            "2.1. Продавець зобов’язується передати у власність Покупця товар, а Покупець — оплатити та прийняти його на умовах цього договору.",
            "2.2. Найменування, кількість і ціна товару визначаються в замовленні, підтвердженому менеджером.",
        ),
    ),
    (
        "3. Ціна та оплата",
        (
            "3.1. Ціни на сайті вказані в гривнях. Вартість доставки не входить у ціну товару, якщо інше не зазначено.",
            "3.2. Покупець оплачує замовлення одним зі способів, наведених у розділі «Доставка і оплата».",
        ),
    ),
    (
        "4. Доставка та приймання",
        (
            "4.1. Право власності та ризик випадкового пошкодження переходять до Покупця в момент отримання товару.",
            "4.2. Під час отримання Покупець перевіряє комплектність і цілісність товару у присутності представника перевізника.",
        ),
    ),
    (
        "5. Повернення товару",
        (
            "5.1. Повернення та обмін здійснюються відповідно до Закону України «Про захист прав споживачів» протягом 14 днів з дня отримання товару.",
        ),
    ),
)
OFFER_REQ_TITLE = "6. Реквізити Продавця"
OFFER_LEGAL_BOX = (
    "[ПІБ ФОП]\nРНОКПП: [номер]\nАдреса: м. Київ, [вулиця, будинок]\n"
    "Телефон: 067 00 00 00 · Email: xxx@gmail.com"
)

PRIVACY_INTRO = (
    "Ця політика пояснює, які персональні дані ми збираємо, навіщо вони потрібні "
    "та як ми їх захищаємо. Користуючись сайтом, ви погоджуєтеся з її умовами."
)
PRIVACY_COLLECT_TITLE = "Які дані ми збираємо"
PRIVACY_COLLECT = (
    "ім’я, прізвище, номер телефону та email;",
    "адресу доставки або номер відділення перевізника;",
    "технічні дані: тип пристрою, браузер, файли cookie.",
)
PRIVACY_WHY_TITLE = "Навіщо вони потрібні"
PRIVACY_WHY = (
    "Ми використовуємо дані лише для обробки та доставки замовлень, зв’язку з вами "
    "щодо замовлення і покращення роботи сайту. Розсилки надсилаємо тільки за вашою згодою."
)
PRIVACY_WHO_TITLE = "Кому ми їх передаємо"
PRIVACY_WHO = (
    "Дані передаються лише службам доставки та платіжним сервісам у обсязі, "
    "необхідному для виконання замовлення. Ми не продаємо персональні дані третім особам."
)
PRIVACY_RIGHTS_TITLE = "Ваші права"
PRIVACY_RIGHTS = (
    "Ви можете в будь-який момент запросити перегляд, виправлення або видалення "
    "своїх даних, написавши на xxx@gmail.com. Ми відповімо протягом 30 днів."
)
PRIVACY_CALLOUT = (
    "Дані зберігаються відповідно до Закону України «Про захист персональних даних» "
    "не довше, ніж це потрібно для мети їх обробки."
)

OFFER_OLD_KEYS = (
    "offer_intro",
    "offer_sec_1_title",
    "offer_sec_1_p1",
    "offer_sec_1_p2",
    "offer_sec_2_title",
    "offer_sec_2_p1",
    "offer_sec_2_p2",
    "offer_sec_3_title",
    "offer_sec_3_p1",
    "offer_sec_3_p2",
    "offer_sec_4_title",
    "offer_sec_4_p1",
    "offer_sec_4_p2",
    "offer_sec_5_title",
    "offer_sec_5_p1",
    "offer_sec_6_title",
    "offer_legal_box",
)
PRIVACY_OLD_KEYS = (
    "privacy_intro",
    "privacy_collect_title",
    "privacy_collect_1",
    "privacy_collect_2",
    "privacy_collect_3",
    "privacy_why_title",
    "privacy_why",
    "privacy_who_title",
    "privacy_who",
    "privacy_rights_title",
    "privacy_rights",
    "privacy_callout",
)

_TRAIL_ONES = re.compile(r"(?<!\d)1+$")


def _loc(text: str, lang: str) -> str:
    if lang == "ru":
        return RU_MAP.get(text, text)
    return text


def _p(text: str) -> str:
    return f"<p>{escape(text)}</p>"


def _h2(text: str) -> str:
    return f"<h2>{escape(text)}</h2>"


def default_offer_html(lang: str = "ua") -> str:
    t = lambda s: _loc(s, lang)  # noqa: E731
    parts = [_p(t(OFFER_INTRO))]
    for title, paras in OFFER_SECTIONS:
        parts.append(_h2(t(title)))
        for para in paras:
            parts.append(_p(t(para)))
    parts.append(_h2(t(OFFER_REQ_TITLE)))
    box = escape(t(OFFER_LEGAL_BOX)).replace("\n", "<br>")
    parts.append(f"<blockquote>{box}</blockquote>")
    return "\n".join(parts)


def default_privacy_html(lang: str = "ua") -> str:
    t = lambda s: _loc(s, lang)  # noqa: E731
    items = "".join(f"<li>{escape(t(item))}</li>" for item in PRIVACY_COLLECT)
    parts = [
        _p(t(PRIVACY_INTRO)),
        _h2(t(PRIVACY_COLLECT_TITLE)),
        f"<ul>{items}</ul>",
        _h2(t(PRIVACY_WHY_TITLE)),
        _p(t(PRIVACY_WHY)),
        _h2(t(PRIVACY_WHO_TITLE)),
        _p(t(PRIVACY_WHO)),
        _h2(t(PRIVACY_RIGHTS_TITLE)),
        _p(t(PRIVACY_RIGHTS)),
        f'<p class="info-callout">{escape(t(PRIVACY_CALLOUT))}</p>',
    ]
    return "\n".join(parts)


def clean_legal_fragment(text: str) -> str:
    return _TRAIL_ONES.sub("", (text or "").strip()).strip()


def _href_allowed(value: str) -> bool:
    href = (value or "").strip()
    if not href:
        return False
    lower = href.lower()
    if lower.startswith(("https:", "http:", "mailto:", "tel:")):
        return True
    return href.startswith(("/", "./", "../", "#"))


def sanitize_legal_html(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    if not re.search(r'<[a-zA-Z/!][^>]*>', text):
        text = linebreaks(text, autoescape=True)
    try:
        root = lhtml.fromstring(f"<div>{text}</div>")
    except Exception:
        return escape(text)
    for el in list(root.iter()):
        tag = el.tag.lower() if isinstance(el.tag, str) else ""
        if el is root:
            continue
        if tag not in ALLOWED_TAGS:
            el.drop_tag()
            continue
        allowed = ALLOWED_ATTR.get(tag, frozenset())
        for attr in list(el.attrib):
            if attr not in allowed:
                del el.attrib[attr]
            elif attr == "href" and not _href_allowed(str(el.attrib[attr])):
                del el.attrib[attr]
    return "".join(
        lhtml.tostring(child, encoding="unicode", method="html") for child in root
    ).strip()


def is_html_body(text: str) -> bool:
    return bool(re.search(r"<[a-z][\s\S]*>", text or "", re.I))


def plain_text_to_html(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    if is_html_body(raw):
        return sanitize_legal_html(raw)
    blocks = [
        re.sub(r"\s+", " ", block).strip()
        for block in re.split(r"\n\s*\n", raw)
    ]
    blocks = [block for block in blocks if block]
    return "\n".join(f"<p>{escape(block)}</p>" for block in blocks)


def compose_offer_from_values(values: dict[str, str]) -> str:
    def g(key: str, fallback: str = "") -> str:
        return clean_legal_fragment(values.get(key) or fallback)

    parts: list[str] = []
    intro = g("offer_intro", OFFER_INTRO)
    if intro:
        parts.append(_p(intro))
    counts = {1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 0}
    for i in range(1, 7):
        title = g(f"offer_sec_{i}_title")
        paras = [
            g(f"offer_sec_{i}_p{j}")
            for j in range(1, counts[i] + 1)
            if g(f"offer_sec_{i}_p{j}")
        ]
        if not title and not paras:
            continue
        if title:
            parts.append(_h2(title))
        for para in paras:
            parts.append(_p(para))
    box = g("offer_legal_box")
    if box:
        if not g("offer_sec_6_title"):
            parts.append(_h2(OFFER_REQ_TITLE))
        parts.append(f"<blockquote>{escape(box).replace(chr(10), '<br>')}</blockquote>")
    return "\n".join(parts) if parts else default_offer_html("ua")


def compose_privacy_from_values(values: dict[str, str]) -> str:
    def g(key: str, fallback: str = "") -> str:
        return clean_legal_fragment(values.get(key) or fallback)

    parts: list[str] = []
    intro = g("privacy_intro", PRIVACY_INTRO)
    if intro:
        parts.append(_p(intro))
    collect_title = g("privacy_collect_title", PRIVACY_COLLECT_TITLE)
    items = [
        g(f"privacy_collect_{i}")
        for i in range(1, 4)
        if g(f"privacy_collect_{i}")
    ]
    if collect_title:
        parts.append(_h2(collect_title))
    if items:
        parts.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>")
    pairs = (
        ("privacy_why_title", "privacy_why", PRIVACY_WHY_TITLE, PRIVACY_WHY),
        ("privacy_who_title", "privacy_who", PRIVACY_WHO_TITLE, PRIVACY_WHO),
        ("privacy_rights_title", "privacy_rights", PRIVACY_RIGHTS_TITLE, PRIVACY_RIGHTS),
    )
    for title_key, body_key, title_fb, body_fb in pairs:
        title = g(title_key, title_fb)
        body = g(body_key, body_fb)
        if title:
            parts.append(_h2(title))
        if body:
            parts.append(_p(body))
    callout = g("privacy_callout", PRIVACY_CALLOUT)
    if callout:
        parts.append(f'<p class="info-callout">{escape(callout)}</p>')
    return "\n".join(parts) if parts else default_privacy_html("ua")
