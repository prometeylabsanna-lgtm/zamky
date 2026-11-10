"""Інфо CMS: about, delivery, warranty, returns — labels + UA defaults."""

from __future__ import annotations

LABELS: dict[tuple[str, str], str] = {}
DEFAULTS: dict[tuple[str, str], str] = {}
INLINE: set[tuple[str, str]] = set()
MULTILINE: set[tuple[str, str]] = set()
RICHTEXT: set[tuple[str, str]] = set()


def _reg(
    page: str,
    key: str,
    label: str,
    default: str,
    *,
    kind: str = "multiline",
) -> None:
    pair = (page, key)
    LABELS[pair] = label
    DEFAULTS[pair] = default
    if kind == "inline":
        INLINE.add(pair)
    elif kind == "richtext":
        RICHTEXT.add(pair)
    else:
        MULTILINE.add(pair)


def _common_head(page: str, title: str, lead: str) -> None:
    _reg(page, f"{page}_section_visible", "Показувати сторінку", "1", kind="inline")
    _reg(page, f"{page}_title", "Заголовок", title, kind="inline")
    _reg(page, f"{page}_lead", "Лід", lead)
    _reg(page, f"{page}_seo_title", "SEO title", title, kind="inline")
    _reg(page, f"{page}_seo_description", "SEO description", lead)


# --- about ---
_common_head(
    "about",
    "Про нас",
    "Ми продаємо замки, серцевини та фурнітуру для дверей і меблів у Києві та по всій Україні. "
    "Допомагаємо підібрати механізм під конкретні двері і пояснюємо різницю між моделями простими словами.",
)
_reg("about", "about_card_1_title", "Картка 1 — заголовок", "Оригінальна продукція", kind="inline")
_reg(
    "about",
    "about_card_1_text",
    "Картка 1 — текст",
    "Працюємо напряму з дистриб’юторами Mottura, Cisa, Kale, Apecs та інших брендів.",
)
_reg("about", "about_card_2_title", "Картка 2 — заголовок", "Підбір під ваші двері", kind="inline")
_reg(
    "about",
    "about_card_2_text",
    "Картка 2 — текст",
    "Підкажемо розмір циліндра, клас захисту та сумісність із замком.",
)
_reg("about", "about_card_3_title", "Картка 3 — заголовок", "Монтаж і сервіс", kind="inline")
_reg(
    "about",
    "about_card_3_text",
    "Картка 3 — текст",
    "Встановлюємо та замінюємо замки, виготовляємо ключі за кодовою карткою.",
)
_reg("about", "about_how_title", "Секція «Як працюємо» — заголовок", "Як ми працюємо", kind="inline")
_reg(
    "about",
    "about_how_body",
    "Секція «Як працюємо» — текст",
    "Кожне замовлення перевіряє менеджер: уточнює розміри, наявність і зручний спосіб доставки. "
    "Якщо ви не впевнені в розмірі, надішліть фото торця дверей — ми допоможемо виміряти.",
)
_reg(
    "about",
    "about_bullet_1",
    "Булет 1",
    "Відправляємо замовлення в день оплати, якщо воно оформлене до 16:00.",
)
_reg("about", "about_bullet_2", "Булет 2", "Надаємо гарантію виробника на всі механізми.")
_reg(
    "about",
    "about_bullet_3",
    "Булет 3",
    "Приймаємо оплату карткою, накладеним платежем і за рахунком для юросіб.",
)
_reg("about", "about_shop_title", "Торгова точка — заголовок", "Торгова точка", kind="inline")
_reg("about", "about_row_1_label", "Рядок 1 — назва", "Адреса", kind="inline")
_reg("about", "about_row_1_value", "Рядок 1 — значення", "м. Київ, [вулиця, будинок]", kind="inline")
_reg("about", "about_row_2_label", "Рядок 2 — назва", "Графік роботи", kind="inline")
_reg("about", "about_row_2_value", "Рядок 2 — значення (hours / текст)", "hours", kind="inline")
_reg("about", "about_row_3_label", "Рядок 3 — назва", "Телефони", kind="inline")
_reg("about", "about_row_3_value", "Рядок 3 — значення (phones / текст)", "phones", kind="inline")
_reg("about", "about_row_4_label", "Рядок 4 — назва", "Email", kind="inline")
_reg("about", "about_row_4_value", "Рядок 4 — значення (email / текст)", "email", kind="inline")

# --- delivery ---
_common_head(
    "delivery",
    "Доставка і оплата",
    "Доставляємо по всій Україні. Замовлення, оформлені до 16:00, відправляємо того ж дня.",
)
_reg("delivery", "delivery_methods_title", "Способи доставки — заголовок", "Способи доставки", kind="inline")
_reg("delivery", "delivery_head_1", "Таблиця — колонка 1", "Спосіб", kind="inline")
_reg("delivery", "delivery_head_2", "Таблиця — колонка 2", "Термін", kind="inline")
_reg("delivery", "delivery_head_3", "Таблиця — колонка 3", "Вартість", kind="inline")
_reg("delivery", "delivery_row_1_a", "Доставка 1 — спосіб", "Нова Пошта, відділення або поштомат", kind="inline")
_reg("delivery", "delivery_row_1_b", "Доставка 1 — термін", "1–2 дні", kind="inline")
_reg("delivery", "delivery_row_1_c", "Доставка 1 — вартість", "80 ₴", kind="inline")
_reg("delivery", "delivery_row_2_a", "Доставка 2 — спосіб", "Кур’єр по Києву", kind="inline")
_reg("delivery", "delivery_row_2_b", "Доставка 2 — термін", "в день замовлення", kind="inline")
_reg("delivery", "delivery_row_2_c", "Доставка 2 — вартість", "150 ₴", kind="inline")
_reg("delivery", "delivery_row_3_a", "Доставка 3 — спосіб", "Самовивіз з магазину", kind="inline")
_reg("delivery", "delivery_row_3_b", "Доставка 3 — термін", "через 2 години", kind="inline")
_reg("delivery", "delivery_row_3_c", "Доставка 3 — вартість", "Безкоштовно", kind="inline")
_reg(
    "delivery",
    "delivery_note",
    "Примітка до доставки",
    "Вартість доставки Новою Поштою може відрізнятися залежно від ваги та габаритів посилки — "
    "точну суму менеджер назве під час підтвердження.",
)
_reg("delivery", "delivery_pay_title", "Оплата — заголовок", "Способи оплати", kind="inline")
_reg("delivery", "delivery_pay_1_title", "Оплата 1 — заголовок", "Карткою онлайн", kind="inline")
_reg(
    "delivery",
    "delivery_pay_1_text",
    "Оплата 1 — текст",
    "Visa, Mastercard, Apple Pay, Google Pay. Оплата після підтвердження замовлення.",
)
_reg("delivery", "delivery_pay_2_title", "Оплата 2 — заголовок", "Накладений платіж", kind="inline")
_reg(
    "delivery",
    "delivery_pay_2_text",
    "Оплата 2 — текст",
    "Оплата у відділенні після огляду товару. Комісію перевізника сплачує отримувач.",
)
_reg("delivery", "delivery_pay_3_title", "Оплата 3 — заголовок", "Безготівковий", kind="inline")
_reg(
    "delivery",
    "delivery_pay_3_text",
    "Оплата 3 — текст",
    "Рахунок для юридичних осіб і ФОП. Відправка після надходження коштів.",
)
_reg("delivery", "delivery_return_title", "Обмін — заголовок", "Обмін та повернення", kind="inline")
_reg(
    "delivery",
    "delivery_return_body",
    "Обмін — текст",
    "Ви можете обміняти або повернути товар протягом 14 днів з моменту отримання, "
    "якщо він не був у використанні, збережено упаковку, ключі та кодову картку.",
)
_reg(
    "delivery",
    "delivery_step_1",
    "Крок 1",
    "Зателефонуйте або напишіть нам і вкажіть номер замовлення.",
)
_reg(
    "delivery",
    "delivery_step_2",
    "Крок 2",
    "Надішліть товар Новою Поштою на реквізити, які надасть менеджер.",
)
_reg(
    "delivery",
    "delivery_step_3",
    "Крок 3",
    "Ми повернемо кошти протягом 3 робочих днів після отримання й перевірки товару.",
)

# --- warranty ---
_common_head(
    "warranty",
    "Гарантія",
    "На всі товари діє офіційна гарантія виробника. "
    "Допомагаємо з ремонтом та заміною без зайвих формальностей.",
)
_reg("warranty", "warranty_card_1_value", "Картка 1 — значення", "12 міс.", kind="inline")
_reg("warranty", "warranty_card_1_title", "Картка 1 — заголовок", "Механічні замки", kind="inline")
_reg(
    "warranty",
    "warranty_card_1_text",
    "Картка 1 — текст",
    "Замки, циліндри, фурнітура, броненакладки",
)
_reg("warranty", "warranty_card_2_value", "Картка 2 — значення", "24 міс.", kind="inline")
_reg("warranty", "warranty_card_2_title", "Картка 2 — заголовок", "Електроніка", kind="inline")
_reg("warranty", "warranty_card_2_text", "Картка 2 — текст", "Кодові замки та контроль доступу")
_reg("warranty", "warranty_card_3_value", "Картка 3 — значення", "12 міс.", kind="inline")
_reg("warranty", "warranty_card_3_title", "Картка 3 — заголовок", "На роботи", kind="inline")
_reg("warranty", "warranty_card_3_text", "Картка 3 — текст", "Встановлення нашими майстрами")
_reg(
    "warranty",
    "warranty_steps_title",
    "Кроки — заголовок",
    "Як скористатися гарантією",
    kind="inline",
)
_reg("warranty", "warranty_step_1_title", "Крок 1 — заголовок", "Звʼяжіться з нами", kind="inline")
_reg("warranty", "warranty_step_1_text", "Крок 1 — текст", "Телефоном, у Viber чи Telegram")
_reg("warranty", "warranty_step_2_title", "Крок 2 — заголовок", "Опишіть проблему", kind="inline")
_reg("warranty", "warranty_step_2_text", "Крок 2 — текст", "Надішліть фото або відео несправності")
_reg("warranty", "warranty_step_3_title", "Крок 3 — заголовок", "Діагностика", kind="inline")
_reg("warranty", "warranty_step_3_text", "Крок 3 — текст", "До 3 робочих днів")
_reg("warranty", "warranty_step_4_title", "Крок 4 — заголовок", "Ремонт або заміна", kind="inline")
_reg("warranty", "warranty_step_4_text", "Крок 4 — текст", "Безкоштовно за гарантійним випадком")
_reg(
    "warranty",
    "warranty_exclude_title",
    "Виключення — заголовок",
    "Гарантія не поширюється",
    kind="inline",
)
_reg("warranty", "warranty_exclude_1", "Виключення 1", "Механічні пошкодження та сліди спроби злому")
_reg("warranty", "warranty_exclude_2", "Виключення 2", "Неправильний монтаж сторонніми особами")
_reg("warranty", "warranty_exclude_3", "Виключення 3", "Вплив вологи, хімії та агресивного середовища")
_reg("warranty", "warranty_exclude_4", "Виключення 4", "Природний знос покриття")

# --- returns ---
_common_head(
    "returns",
    "Обмін та повернення",
    "Ви можете повернути або обміняти товар протягом 14 днів з моменту покупки.",
)
_reg("returns", "returns_steps_title", "Кроки — заголовок", "Як повернути товар", kind="inline")
_reg("returns", "returns_step_1_title", "Крок 1 — заголовок", "Напишіть нам", kind="inline")
_reg("returns", "returns_step_1_text", "Крок 1 — текст", "Вкажіть номер замовлення та причину")
_reg("returns", "returns_step_2_title", "Крок 2 — заголовок", "Відправте товар", kind="inline")
_reg("returns", "returns_step_2_text", "Крок 2 — текст", "Новою поштою або привезіть у магазин")
_reg("returns", "returns_step_3_title", "Крок 3 — заголовок", "Перевірка", kind="inline")
_reg("returns", "returns_step_3_text", "Крок 3 — текст", "Огляд товару протягом 1 дня")
_reg("returns", "returns_step_4_title", "Крок 4 — заголовок", "Повернення коштів", kind="inline")
_reg("returns", "returns_step_4_text", "Крок 4 — текст", "Протягом 3 робочих днів")
_reg("returns", "returns_terms_title", "Умови — заголовок", "Умови повернення", kind="inline")
_reg("returns", "returns_terms_1", "Умова 1", "Товар не був у використанні та не встановлювався")
_reg("returns", "returns_terms_2", "Умова 2", "Збережено упаковку, комплектацію та пломби")
_reg("returns", "returns_terms_3", "Умова 3", "Є чек або номер замовлення")
_reg(
    "returns",
    "returns_no_title",
    "Не повертаються — заголовок",
    "Не підлягають поверненню",
    kind="inline",
)
_reg(
    "returns",
    "returns_no_body",
    "Не повертаються — текст",
    "Циліндри з індивідуальною картою власника, товари, виготовлені під замовлення, "
    "а також товари з порушеною заводською пломбою.",
)
