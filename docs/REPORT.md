# Звіт: e-commerce «Замки»

## Структура

```
Замки/
├── E-com/                 # оригінальний дизайн (checkpoint)
├── config/                # settings, urls, districts.json
├── catalog/               # Category, Product, атрибути, зображення, seed
├── cart/                  # сесійний кошик + wishlist
├── orders/                # Order, OrderItem, райони, checkout
├── pages/                 # info-сторінки, context processors
├── templates/             # base + partials + сторінки
├── static/                # css/, js/, vendor/htmx, img/
├── media/                 # завантажені зображення товарів
├── docs/REPORT.md
├── requirements.txt
├── .env.example
└── manage.py
```

## Як запустити

```bash
cd /Users/olegbonislavskyi/Sites/Замки
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # або використати наявний .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Адмінка: `/admin/` (потрібно створити суперкористувача: `python manage.py createsuperuser`).

## Що зроблено

- Дизайн-система з E-com у CSS custom properties (`static/css/*`), mobile-first, Inter + акцент `#ffc400`.
- Бекенд: каталог (дерево категорій, атрибути, зображення), сесійний кошик/обране, замовлення з районами з `districts.json`.
- Checkout: валідація форм, перевірка stock, `idempotency_key` + `transaction.atomic` + `select_for_update` зі списанням залишку.
- HTMX 2.x (вендорний файл): фільтри/сортування каталогу, кошик, wishlist, оновлення лічильника.
- Unfold-адмінка з inlines.
- Seed `seed_demo` (~45 товарів з дизайну).
- Тести: кошик, stock, idempotency checkout, фільтри — зелені.
- Сторінки `/`, `/catalog/`, `/product/<slug>/`, `/checkout/`, `/info/...` повертають 200.
- Скріншоти: `Замки_context/screens/` (desktop 1440 і mobile 390).

## Що лишилось / ризики

- Пошук у хедері — GET на каталог; без живої підказки/autocomplete.
- Оплата — лише вибір методу (без інтеграції еквайрингу).
- Відгуки/рейтинг на картці — статичний UI з дизайну.
- Фільтр ціни — інпути без drag-range з макета.
- Cart/checkout скріншоти можуть показувати порожній кошик, якщо сесію не підхоплено headless Chrome.
- Для production потрібні сильний `SECRET_KEY`, `DEBUG=False`, HTTPS, Postgres, збір static.
