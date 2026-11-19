"""Скидання кешу фідів при зміні каталогу чи налаштувань фіду."""

from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from catalog.models import Category, Product, ProductAttribute, ProductImage
from marketing.feeds import bump_feeds_version
from marketing.models import FeedCategoryMapping, ProductFeed, SeoSettings

_WATCHED = (Product, ProductImage, ProductAttribute, Category, ProductFeed, FeedCategoryMapping, SeoSettings)


def _bump(sender, **kwargs):
    bump_feeds_version()


for _model in _WATCHED:
    post_save.connect(_bump, sender=_model, dispatch_uid=f"marketing_feed_save_{_model.__name__}")
    post_delete.connect(_bump, sender=_model, dispatch_uid=f"marketing_feed_del_{_model.__name__}")


@receiver(m2m_changed, sender=ProductFeed.categories.through, dispatch_uid="marketing_feed_m2m")
def _feed_categories_changed(sender, **kwargs):
    bump_feeds_version()
