# Товарні фіди — контракт (Zamky)

Статус: чернетка CMS 2026-11-19, на узгодження з Integrations. Код: `marketing/feeds.py`, `marketing/views.py`.

## URL і доступ

| | |
|---|---|
| URL | `/feeds/<slug>.xml` (поза `i18n_patterns`, без мовного префікса) |
| Слаг | випадковий: `<тип>-<16 hex>`, редагується в адмінці |
| Закриття | необовʼязковий `?token=…` (перевірка `secrets.compare_digest`); невірний/відсутній → 404 |
| Вимкнений фід | 404 |
| Відповідь | `Content-Type: application/xml; charset=utf-8`, `ETag`, `Last-Modified`, `If-None-Match` → 304, `X-Robots-Tag: noindex` |
| Кеш | Django cache, 1–6 год (поле `cache_hours`, дефолт 3). Скидається при save/delete Product, ProductImage, ProductAttribute, Category, ProductFeed, мапінгу категорій, SeoSettings (версія `marketing_feeds_version`) |
| Генерація | на льоту + `python manage.py generate_feeds [--slug …] [--output DIR] [--base-url https://…] [--include-disabled]` |
| Журнал | `enabled_changed_at` / `enabled_changed_by` + стандартний LogEntry адмінки |

Фід — не sitemap. Домен для абсолютних URL: «Маркетинг → SEO → Основний домен»; якщо порожній — host запиту (лише для локальної перевірки).

## Модель `marketing.ProductFeed`

`name`, `feed_type` (google | facebook | prom), `slug`, `is_enabled` (дефолт False — усі три сід-фіди вимкнені, Prom теж), `access_token`, `shop_name`, `company_name`, `currency` (UAH/USD/EUR), `only_in_stock`, `categories` (M2M, порожньо = весь каталог, підкатегорії включаються), `cache_hours`, статистика `last_generated_at/last_included/last_excluded/last_excluded_reasons`.
`marketing.FeedCategoryMapping`: `feed`, `category`, `google_product_category` (числовий ID; береться найближчий мапінг вгору по дереву).

Каталог (`catalog.Product/Category`) лише читається; схема каталогу не змінювалась.

## Вибірка (один queryset)

`Product.objects.filter(is_active=True)` + `select_related(category, family)` + `prefetch(images за sort_order, product_attributes→attribute_value→attribute)`, `.iterator(chunk_size=500)`; категорії — одним запитом у словник.

Виключення (лічильник у адмінці «Статистика»):

| причина | правило |
|---|---|
| `price_not_positive` | price ≤ 0 |
| `below_purchase_price` | price < закупівля — **поля закупівлі в каталозі немає**, хук `getattr(product, "purchase_price")` |
| `inactive_category` | категорія товару `is_active=False` |
| `no_image` | немає жодного ProductImage |
| `no_link` | немає slug |
| (фільтр) | `only_in_stock` → `stock > 0`; категорії → queryset, у лічильник не входять |

Неактивні товари відсікаються queryset-ом і в лічильник не входять.

## Google Merchant / Facebook Catalog — RSS 2.0 + `xmlns:g="http://base.google.com/ns/1.0"`

Обидва типи віддають однаковий XML (Meta приймає Google RSS).

| g: поле | джерело | правило |
|---|---|---|
| `id` | `Product.sku` | стабільний, не залежить від назви/slug |
| `title` | `Product.name` (UA) | ≤ 150 символів, plain text (XML-екранування lxml) |
| `description` | `description` → `short_description` → `name` | strip HTML, unescape, згорнуті пробіли, ≤ 5000 |
| `link` | домен + `/ua/product/<slug>/` | абсолютний; https, якщо домен https |
| `image_link` | перше ProductImage (sort_order, id) | абсолютний |
| `additional_image_link` | наступні до 10 | |
| `availability` | `stock > 0` → `in_stock`, інакше `out_of_stock` | preorder/backorder у каталозі немає |
| `price` | `Decimal.quantize(0.01)` + `" " + feed.currency` | якщо `old_price > price`: `price = old_price`, `sale_price = price` |
| `sale_price` | див. вище | |
| `condition` | `new` | |
| `brand` | `Product.brand` → `ProductFamily.brand` | порожній — не виводиться |
| `gtin` | `getattr(product, "gtin")`, лише 8/12/13/14 цифр | **у каталозі поля немає** → не виводиться; sku ніколи не підставляється |
| `mpn` | `getattr(product, "mpn")` | **у каталозі поля немає** |
| `identifier_exists` | `no`, якщо немає gtin і немає пари brand+mpn | зараз `no` для всіх |
| `google_product_category` | `FeedCategoryMapping` | необовʼязково |
| `product_type` | ланцюжок категорій `Корінь > Дочірня` | |

Канал: `title`/`description` = `shop_name`, `link` = домен. Shipping і tax не виводяться.

## Prom.ua — YML (`feed_type=prom`, дефолт вимкнено)

```
yml_catalog@date="YYYY-MM-DD HH:MM" (Europe/Kyiv)
  shop/name, shop/company (company_name → shop_name), shop/url
  shop/currencies/currency@id=<currency>@rate=1
  shop/categories/category@id@parentId (лише категорії товарів фіду + предки)
  shop/offers/offer@id=<sku>@available=true|false
    url, price (поточна ціна продажу, Decimal 0.01), currencyId, categoryId,
    picture ×N (до 11), name, vendor, vendorCode=<sku>,
    description (CDATA, plain text), param@name ×N (фільтри каталогу), quantity_in_stock
```

## Що не виводиться ніколи

Закупівельна ціна, постачальник, внутрішні поля (stock виводиться лише як `quantity_in_stock` у Prom), токени.

## Відкриті питання для Integrations / DB

- [ ] Поля `gtin` (EAN), `mpn`, `purchase_price` у каталозі — зона DB; після появи фід підхопить їх без змін (через `getattr`).
- [ ] Prom: `offer@id` = sku (з дефісами) — чи ок для Prom, чи потрібен числовий id; чи потрібен `oldprice`.
- [ ] Google `availability`: використано `in_stock`/`out_of_stock` (з підкресленням, як у вимогах).
- [ ] Мова фіду: UA (назви з БД). RU-фід за потреби — окремий тип/поле `language`.
- [ ] `google_product_category` ID для категорій сайту — заповнити мапінг.

## Перевірка

`python manage.py generate_feeds --include-disabled --output /tmp/feeds --base-url https://… && xmllint --noout /tmp/feeds/*.xml` — 2026-11-19 локально: 3 фіди × 62 товари, xmllint OK. Тести: `marketing/tests.py` (екранування, ціна/валюта, sale_price, виключення, identifier_exists, фільтри, 404/token/ETag, кеш, YML).
