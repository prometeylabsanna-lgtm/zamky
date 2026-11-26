# SEO-налаштування — нотатки для SEO (Zamky)

Статус: CMS 2026-11-19, вимоги SEO-бота від 2026-11-19 враховано. Код: `marketing/models.py::SeoSettings`, `marketing/seo.py`, `templates/marketing/seo_head.html`, `templates/base.html`.

**Принцип:** поки поля порожні, HTML сайту байт-у-байт той самий, що до зміни (перевірено diff-ом 7 сторінок ua/ru). Колишній хардкод `<title>` у `base.html` («Центр замків») тепер — сід `title_default` + фолбек у коді.

## Поля (Маркетинг → SEO-налаштування, singleton)

| Поле | Вивід | Правило |
|---|---|---|
| `primary_domain` | canonical, og:url, абсолютні URL | `^https://домен$`, без слеша. Порожньо → canonical/OG/Twitter/JSON-LD **не виводяться** |
| `title_default`, `title_default_ru` | `<title>` сторінок без власного title | RU порожній → `tr(UA)`; max 255, попередження > 60 з суфіксом |
| `title_suffix` | « \| Бренд» | не додається, якщо title уже містить бренд (без «Бренд \| Бренд») |
| `description_default`, `_ru` | `<meta name=description>`, og:description | max 300; попередження < 70 або > 160 |
| `og_image`, `og_image_alt` | og:image (+width/height/alt) | мін. 600×315 (валідація), попередження якщо ≠ 1200×630; alt ≤ 125 |
| `twitter_card` | twitter:card | дефолт summary_large_image; title/description беруться з OG |
| `twitter_site` | twitter:site | `@handle`, необовʼязково |
| `global_noindex` | `<meta name="robots" content="noindex, nofollow">` на всіх сторінках | великий червоний банер в адмінці; robots.txt НЕ отримує `Disallow: /` (щоб бот побачив noindex) |
| `robots_extra` | рядки в кінці `/robots.txt` | лише User-agent/Allow/Disallow/Crawl-delay/Sitemap/# ; автоматичні рядки не затираються |
| `google_verification`, `bing_verification`, `meta_domain_verification`, `pinterest_verification` | `<meta name=… content=…>` | лише значення content, `^[A-Za-z0-9_-]+$` |
| `org_type` (Organization / LocalBusiness), `org_name`, `org_logo`, `same_as` | JSON-LD лише на головній `/ua/`, `/ru/` | логотип ≥ 112×112; порожня властивість не виводиться; telephone/email/address/соцмережі — з «Налаштування → Контакти» |

Лічильник символів біля title/description/alt — `static/js/admin/seo_counter.js`; попередження ще й через messages при збереженні. Нічого не блокується.

## Пріоритет

1. Сторінкові поля: `Product.seo_title(_ru)`, `seo_description(_ru)`, `canonical_url`, `og_image` (поля були в моделі, але раніше не виводились — тепер мають пріоритет; локально всі порожні).
2. Контекст `seo_title` / `seo_description` / `seo_canonical` з view (для майбутніх сторінок).
3. `{% block title %}` шаблону.
4. Дефолти SeoSettings → фолбек «Центр замків».

## Canonical

`primary_domain + request.path` (без query/utm, trailing slash як у Django-URL). `Product.canonical_url` — лише перевизначення (https:// або /шлях). canonical = og:url. `/ua/info/` канонікалізується на `/ua/info/about/`. Пошук (`?q=`, `?sku=`) і сторінки районів/міста **без canonical**. Фільтри/сортування/пагінація: canonical на чистий path.

## noindex

Сторінковий `noindex, follow`: кошик, обране, чекаут, замовлення, API, submit-форми, `/kyiv/`, пошук, фасети (`sort`, ціна, атрибути, `limit`, `page`). Глобальний прапор лишається `noindex, nofollow`. `robots.txt` не отримує `Disallow: /`.

## Sitemap і llms.txt

- `/sitemap.xml` (`name=sitemap`): головні ua/ru, каталог, активні категорії/товари, видимі інфо-сторінки, опубліковані статті. Без районів, кошика, чекауту, фільтрів. hreflang ua→`uk`, ru, `x-default`.
- `/robots.txt`: `Disallow` для `/admin/`, `/feeds/`, `/healthz/`, `/lang/`, мовних `cart/`, `checkout/`, `order/`, `api/`, `callback/`, `photo-pick/`, `install/` (не `/info/install/`). `Sitemap:` додається автоматично. CSS/JS/медіа не закриті.
- `/llms.txt`: факти з CMS, категорій, статей і контактів (порожні поля не вигадуються).

## Мови

ua/ru (префікси `/ua/`, `/ru/`). og:locale `uk_UA` / `ru_RU`, og:locale:alternate — друга мова. hreflang (`uk` / `ru` / `x-default`) лише на індексованих URL і лише з `primary_domain`. Корінь `/` — постійний редірект на `/ua/`.

## JSON-LD

На головній: Organization/LocalBusiness (як раніше). На картці товару: Product (name, sku, price, availability, image, url; AggregateRating лише з реальних опублікованих відгуків). BreadcrumbList там, де в HTML є крихти. Без SearchAction/HowTo/FAQPage. Екранування `<>&` як у `json_script`.

## Перенесення

`SiteSettings.meta_title/meta_description(_ru)` (раніше в адмінці «Контакти та SEO», але **ніде не виводились**) копіюються сідом `marketing/0002` у SeoSettings, якщо там порожньо. Fieldset прибрано з «Налаштування», поля в БД лишились. Якщо на проді вони заповнені — після міграції зʼявиться meta description / зміниться дефолтний title: перевірити перед деплоєм.

## CSP

CSP у проєкті немає. Якщо зʼявиться: пікселі потребують `script-src` для `www.googletagmanager.com`, `connect.facebook.net`, `analytics.tiktok.com` + inline-скриптів (nonce), `img-src`/`connect-src` для `www.google-analytics.com`, `www.facebook.com`, `analytics.tiktok.com`; `frame-src www.googletagmanager.com` (GTM noscript).

## Пікселі (Маркетинг → Пікселі та лічильники)

GA4 `^G-[A-Z0-9]{4,16}$`, GTM `^GTM-[A-Z0-9]{4,12}$`, Google Ads `^AW-[0-9]{6,15}$`, Meta `^[0-9]{6,20}$`, TikTok `^[A-Z0-9]{10,32}$`. Вивід лише якщо увімкнено **і** ID валідний (повторна перевірка під час рендеру). Сніпети фіксовані в `templates/marketing/tracking_head.html` / `tracking_body.html`; довільний HTML/JS з адмінки не приймається. Наявних хардкоджених трекерів у шаблонах не було — переносити нічого.
