"""Пошук каталогу з урахуванням кирилиці (SQLite) + легкий fuzzy."""

from __future__ import annotations

from django.db.models import Case, IntegerField, When

from catalog.models import Category, Product


def norm(text: str) -> str:
    return (text or '').casefold().replace('ё', 'е').replace('’', "'").strip()


def _tokens(text: str) -> list[str]:
    raw = norm(text).replace('-', ' ').replace('/', ' ').replace('*', ' ')
    return [t for t in raw.split() if t]


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if abs(len(a) - len(b)) > 2:
        return 99
    if len(a) > len(b):
        a, b = b, a
    prev = list(range(len(a) + 1))
    for j, bj in enumerate(b, start=1):
        cur = [j]
        for i, ai in enumerate(a, start=1):
            ins = cur[i - 1] + 1
            delete = prev[i] + 1
            sub = prev[i - 1] + (ai != bj)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1]


def _word_score(word: str, q: str) -> int:
    if not word or not q:
        return 0
    if word == q:
        return 100
    if word.startswith(q):
        return 90
    if q in word:
        return 70
    # префікс запиту ≈ початок слова (недописане)
    if len(q) >= 2 and word.startswith(q[: max(2, len(q) - 1)]):
        return 55
    max_dist = 1 if len(q) <= 4 else 2
    if len(word) >= 3 and _levenshtein(word[: len(q) + 1], q) <= max_dist:
        return 45
    if len(q) >= 3 and _levenshtein(word, q) <= max_dist:
        return 40
    return 0


def _haystacks(product: Product) -> list[str]:
    cat = product.category.name if getattr(product, 'category_id', None) and product.category else ''
    return [
        product.name or '',
        product.sku or '',
        product.brand or '',
        cat,
        product.color_label or '',
        product.short_description or '',
    ]


def score_product(product: Product, query: str) -> int:
    q = norm(query)
    if not q:
        return 0
    q_tokens = _tokens(q) or [q]
    best = 0
    for hay in _haystacks(product):
        hn = norm(hay)
        if not hn:
            continue
        if hn == q:
            best = max(best, 120)
            continue
        if q in hn:
            best = max(best, 95 if hn.startswith(q) else 80)
        words = _tokens(hn)
        token_hits = 0
        token_score = 0
        for qt in q_tokens:
            local = 0
            for w in words:
                local = max(local, _word_score(w, qt))
            if local:
                token_hits += 1
                token_score += local
        if token_hits:
            # усі токени запиту знайдені — бонус
            bonus = 20 if token_hits == len(q_tokens) else 0
            best = max(best, token_score // max(1, len(q_tokens)) + bonus)
    return best


def _catalog_base_qs():
    return (
        Product.objects.filter(is_active=True, catalog_order__lt=500)
        .exclude(sku__startswith='HOME-')
        .select_related('category')
    )


def ranked_products(query: str, *, limit: int | None = None, min_score: int = 35):
    q = (query or '').strip()
    qs = _catalog_base_qs()
    if not q:
        return qs.none() if limit is not None else qs

    scored: list[tuple[int, Product]] = []
    for product in qs:
        s = score_product(product, q)
        if s >= min_score:
            scored.append((s, product))
    scored.sort(key=lambda item: (-item[0], item[1].catalog_order, item[1].name))
    if limit is not None:
        scored = scored[:limit]
    return scored


def filter_queryset_by_query(qs, query: str, *, min_score: int = 35):
    """Фільтрує queryset за рангом; зберігає порядок релевантності."""
    q = (query or '').strip()
    if not q:
        return qs

    # оцінка по повному каталогу, перетин з поточним qs (категорія/фільтри)
    allowed = set(qs.values_list('pk', flat=True))
    ranked = ranked_products(q, min_score=min_score)
    ids = [p.pk for score, p in ranked if p.pk in allowed]
    if not ids:
        return qs.none()
    preserved = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(ids)],
        output_field=IntegerField(),
    )
    return qs.filter(pk__in=ids).order_by(preserved)


def suggest(query: str, *, limit: int = 8) -> list[dict]:
    q = (query or '').strip()
    if len(norm(q)) < 2:
        return []

    items: list[dict] = []
    seen: set[str] = set()

    def add(key: str, payload: dict):
        if key in seen or len(items) >= limit:
            return
        seen.add(key)
        items.append(payload)

    qn = norm(q)
    for cat in Category.objects.filter(is_active=True).order_by('sort_order', 'name'):
        cn = norm(cat.name)
        if cn.startswith(qn) or qn in cn or _word_score(cn.split()[0] if cn else '', qn):
            add(
                f'cat:{cat.pk}',
                {
                    'type': 'category',
                    'label': cat.name,
                    'meta': 'Категорія',
                    'url': cat.get_absolute_url(),
                },
            )

    brands = (
        Product.objects.filter(is_active=True, catalog_order__lt=500)
        .exclude(sku__startswith='HOME-')
        .exclude(brand='')
        .values_list('brand', flat=True)
        .distinct()
    )
    for brand in brands:
        bn = norm(brand)
        if bn.startswith(qn) or qn in bn or _levenshtein(bn[: len(qn) + 1], qn) <= 1:
            add(
                f'brand:{bn}',
                {
                    'type': 'brand',
                    'label': brand,
                    'meta': 'Бренд',
                    'url': '',  # підставляє SearchSuggestApiView через reverse
                },
            )

    for score, product in ranked_products(q, limit=limit, min_score=30):
        add(
            f'product:{product.pk}',
            {
                'type': 'product',
                'label': product.name,
                'meta': product.brand or product.sku,
                'url': product.get_absolute_url(),
                'score': score,
            },
        )
        if len(items) >= limit:
            break

    return items[:limit]
