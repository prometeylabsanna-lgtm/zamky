"""Лічильник і середня оцінка відгуків товару з активних відгуків."""

from decimal import Decimal

from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.db.utils import OperationalError, ProgrammingError


def quantize_review_avg(raw):
    """Один знак після коми — як f'{avg:.1f}' на картці."""
    if raw is None:
        return None
    return Decimal(f'{float(raw):.1f}')


def sync_product_review_stats(product_id):
    if not product_id:
        return
    from catalog.db_compat import review_table_ready
    from catalog.models import Product, Review

    if not review_table_ready():
        return
    try:
        agg = Review.objects.filter(
            product_id=product_id, is_published=True
        ).aggregate(n=Count('id'), avg=Avg('rating'))
        n = int(agg['n'] or 0)
        avg = quantize_review_avg(agg['avg']) if n else None
        Product.objects.filter(pk=product_id).update(
            reviews_count=n,
            reviews_avg=avg,
        )
    except (OperationalError, ProgrammingError):
        return


def sync_review_stats_for_products(product_ids):
    for pid in {pk for pk in product_ids if pk}:
        sync_product_review_stats(pid)


def _on_review_save(sender, instance, **kwargs):
    sync_product_review_stats(getattr(instance, 'product_id', None))


def _on_review_delete(sender, instance, **kwargs):
    sync_product_review_stats(getattr(instance, 'product_id', None))


def connect_review_signals():
    from catalog.models import Review

    post_save.connect(_on_review_save, sender=Review, dispatch_uid='catalog.review_stats.save')
    post_delete.connect(
        _on_review_delete, sender=Review, dispatch_uid='catalog.review_stats.delete'
    )
