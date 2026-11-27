"""Лістинг каталогу: тип = дерево категорій, бренд = фільтр, не окрема вітрина."""

from catalog.category_tree import (
    BRAND_ROOT_NAMES,
    BRAND_TYPE_SUBS,
    subtree_ids,
)


def _root_of(category):
    node = category
    seen = set()
    while node is not None and node.parent_id and node.pk not in seen:
        seen.add(node.pk)
        node = node.parent
    return node


def listing_scope(category):
    from catalog.models import Category

    if category is None:
        return {'category_ids': None, 'brand': None}
    root = _root_of(category)
    if root is not None and root.name in BRAND_ROOT_NAMES:
        type_ids = None
        if category.pk != root.pk and category.name in BRAND_TYPE_SUBS:
            type_root = Category.objects.filter(
                name=category.name, parent__isnull=True, is_active=True
            ).first()
            if type_root is not None:
                type_ids = subtree_ids(type_root.pk)
        return {'category_ids': type_ids, 'brand': root.name}
    return {'category_ids': subtree_ids(category.pk), 'brand': None}


def apply_listing_scope(qs, scope):
    ids = scope.get('category_ids')
    brand = scope.get('brand')
    if ids is not None:
        qs = qs.filter(category_id__in=ids)
    if brand:
        qs = qs.filter(brand=brand)
    return qs


def category_nav_chips(category):
    if category is None:
        return []
    kids = [
        child
        for child in category.children.filter(is_active=True, show_in_menu=True).order_by(
            'sort_order', 'name'
        )
    ]
    if not kids:
        return []
    return [
        {
            'name': child.card_name(),
            'url': child.get_absolute_url(),
            'active': False,
        }
        for child in kids
    ]
