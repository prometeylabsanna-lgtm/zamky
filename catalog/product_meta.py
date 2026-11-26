"""Підписи рейтингу, відгуків і гарантії на картці товару."""

from django.utils.translation import get_language

from pages.i18n_lib import tr


def _plural(n, one, few, many):
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    a, b = n % 10, n % 100
    if a == 1 and b != 11:
        return one
    if 2 <= a <= 4 and (b < 12 or b > 14):
        return few
    return many


def plural_reviews(n):
    if (get_language() or 'ua')[:2] == 'ru':
        return _plural(n, 'отзыв', 'отзыва', 'отзывов')
    return _plural(n, 'відгук', 'відгуки', 'відгуків')


def plural_months(n):
    if (get_language() or 'ua')[:2] == 'ru':
        return _plural(n, 'месяц', 'месяца', 'месяцев')
    return _plural(n, 'місяць', 'місяці', 'місяців')


def reviews_label(count):
    n = int(count or 0)
    if n <= 0:
        return ''
    return f'· {n} {plural_reviews(n)}'


def warranty_label(months):
    n = int(months or 0)
    if n <= 0:
        return ''
    return f'{tr("Гарантія")} {n} {plural_months(n)}'


def review_summary(product, published=None):
    """Лічильник і середня оцінка з активних відгуків. Немає їх — лише поле «Рейтинг»."""
    if published is None:
        from catalog.db_compat import published_reviews_for

        published = published_reviews_for(product)
    if published:
        n = len(published)
        avg = sum(r.rating for r in published) / n
        return {
            'count': n,
            'rating': round(avg, 1),
            'score': f'{avg:.1f}',
            'stars': int(avg + 0.5),
            'label': reviews_label(n),
            'from_reviews': True,
        }
    rating = int(product.rating or 0)
    return {
        'count': 0,
        'rating': float(rating),
        'score': f'{rating}.0',
        'stars': rating,
        'label': '',
        'from_reviews': False,
    }
