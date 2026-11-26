"""Синхронізація дерева категорій і товарів з макетом меню."""

from pathlib import Path

from django.conf import settings
from django.core.files import File

from catalog.category_tree import (
    CHILD_ALIASES,
    MENU_TREE,
    ROOT_ALIASES,
)

_HIDDEN_ROOTS = ('Guardian', 'Замки підвищеного захисту')


def _src_logo(rel_path):
    if not rel_path:
        return None
    path = Path(settings.BASE_DIR) / 'static' / 'img' / rel_path
    return path if path.exists() else None


def _attach_logo(category, rel_path, force=False):
    src = _src_logo(rel_path)
    if src is None:
        return
    current = (getattr(category.logo, 'name', '') or '').rsplit('/', 1)[-1]
    if not force and current:
        return
    if current == src.name and not force:
        return
    with src.open('rb') as fh:
        category.logo.save(src.name, File(fh), save=True)


def _find_named(old_name):
    from catalog.models import Category

    return (
        Category.objects.filter(name=old_name, parent__isnull=True).first()
        or Category.objects.filter(name=old_name).order_by('pk').first()
    )


def _rename_root(old_name, new_name):
    from catalog.models import Category

    if old_name == new_name:
        return Category.objects.filter(name=new_name, parent__isnull=True).first()
    old = _find_named(old_name)
    existing = Category.objects.filter(name=new_name, parent__isnull=True).first()
    if old is None:
        return existing
    if old.parent_id and (existing is None or existing.pk != old.pk):
        old.parent = None
        old.is_active = True
        old.show_in_menu = True
        old.save(update_fields=['parent', 'is_active', 'show_in_menu'])
    if existing is None:
        old.name = new_name
        old.is_active = True
        old.show_in_menu = True
        old.parent = None
        old.save(update_fields=['name', 'is_active', 'show_in_menu', 'parent'])
        return old
    if existing.pk == old.pk:
        return existing
    return _merge_into(old, existing)


def _merge_into(source, target):
    from catalog.models import Category, Product

    Category.objects.filter(parent=source).update(parent=target)
    Product.objects.filter(category=source).update(category=target)
    source.show_in_menu = False
    source.is_active = False
    source.save(update_fields=['show_in_menu', 'is_active'])
    return target


def _child(parent, name):
    from catalog.models import Category

    return Category.objects.filter(parent=parent, name=name).first()


def _rename_child(parent, old_name, new_name):
    old = _child(parent, old_name)
    if old is None:
        return _child(parent, new_name)
    if old_name == new_name:
        return old
    existing = _child(parent, new_name)
    if existing is None:
        old.name = new_name
        old.save(update_fields=['name'])
        return old
    return _merge_into(old, existing)


def _get_or_create_root(item, sort_order):
    from catalog.models import Category

    name = item['name']
    root = Category.objects.filter(name=name, parent__isnull=True).first()
    if root is None:
        root = Category(name=name, parent=None, is_active=True)
    fields = ['name', 'is_active', 'show_in_menu', 'sort_order']
    root.is_active = True
    root.show_in_menu = True
    root.sort_order = sort_order
    if item.get('name_ru') and root.name_ru != item['name_ru']:
        root.name_ru = item['name_ru']
        fields.append('name_ru')
    lock = (item.get('lock') or '').strip()
    if lock and root.icon != lock:
        root.icon = lock
        fields.append('icon')
    subtitle = item.get('home_subtitle') or ''
    if subtitle and not root.home_subtitle:
        root.home_subtitle = subtitle
        fields.append('home_subtitle')
    if root.pk:
        root.save(update_fields=fields)
    else:
        root.save()
    if item.get('logo'):
        _attach_logo(root, item['logo'])
    return root


def _dedupe_named_children(parent, name):
    from catalog.models import Category

    rows = list(Category.objects.filter(parent=parent, name=name).order_by('pk'))
    if not rows:
        return None
    keep = next((row for row in rows if row.is_active and row.show_in_menu), rows[0])
    for extra in rows:
        if extra.pk != keep.pk:
            _merge_into(extra, keep)
    return keep


def _get_or_create_child(parent, name, sort_order):
    from catalog.models import Category

    node = Category.objects.filter(parent=parent, name=name).first()
    if node is None:
        node = Category(name=name, parent=parent, is_active=True)
    node.is_active = True
    node.show_in_menu = True
    node.sort_order = sort_order
    if node.pk:
        node.save(update_fields=['is_active', 'show_in_menu', 'sort_order'])
    else:
        node.save()
    return _dedupe_named_children(parent, name) or node


def _dedupe_named_roots(name):
    from catalog.models import Category

    rows = list(
        Category.objects.filter(name=name, parent__isnull=True).order_by('pk')
    )
    keep = None
    for row in rows:
        if row.is_active and row.show_in_menu:
            keep = row
            break
    if keep is None and rows:
        keep = rows[0]
        keep.is_active = True
        keep.show_in_menu = True
        keep.save(update_fields=['is_active', 'show_in_menu'])
    for extra in rows:
        if keep is not None and extra.pk != keep.pk:
            _merge_into(extra, keep)
    return keep


def _hide_extra_roots(keep_names):
    from catalog.models import Category

    extras = Category.objects.filter(parent__isnull=True).exclude(name__in=keep_names)
    extras.update(show_in_menu=False)
    for name in _HIDDEN_ROOTS:
        Category.objects.filter(name=name, parent__isnull=True).update(
            show_in_menu=False
        )


def _hide_stale_children(root, wanted_tree):
    from catalog.models import Category

    wanted_l2 = set(wanted_tree.keys())
    for sub in Category.objects.filter(parent=root):
        if sub.name not in wanted_l2:
            sub.show_in_menu = False
            sub.save(update_fields=['show_in_menu'])
            continue
        wanted_l3 = set(wanted_tree[sub.name])
        for leaf in Category.objects.filter(parent=sub):
            if leaf.name not in wanted_l3:
                leaf.show_in_menu = False
                leaf.save(update_fields=['show_in_menu'])


def _allowed_ids():
    from catalog.models import Category

    ids = set()
    for item in MENU_TREE:
        root = Category.objects.filter(name=item['name'], parent__isnull=True).first()
        if root is None:
            continue
        ids.add(root.pk)
        for sub_name, leaves in item['tree'].items():
            sub = Category.objects.filter(parent=root, name=sub_name).first()
            if sub is None:
                continue
            ids.add(sub.pk)
            for leaf_name in leaves:
                leaf = Category.objects.filter(parent=sub, name=leaf_name).first()
                if leaf is not None:
                    ids.add(leaf.pk)
    return ids


def _nearest_menu_category(category, allowed):
    from catalog.models import Category

    node = category
    seen = set()
    while node is not None and node.pk not in seen:
        seen.add(node.pk)
        if node.pk in allowed:
            kids = [
                child
                for child in Category.objects.filter(
                    parent=node, is_active=True, show_in_menu=True
                ).order_by('sort_order', 'name')
                if child.pk in allowed
            ]
            if kids:
                std = next((c for c in kids if c.name == 'Стандартні'), None)
                return std or kids[0]
            return node
        node = node.parent
    return None


def _path_names(category):
    names = []
    node = category
    seen = set()
    while node is not None and node.pk not in seen:
        seen.add(node.pk)
        names.append(node.name)
        node = node.parent
    return names


def _fallback_category(product):
    from catalog.models import Category

    cat = product.category
    if cat is not None:
        names = _path_names(cat)
        if 'Замки підвищеного захисту' in names:
            locks = Category.objects.filter(name='Замки', parent__isnull=True).first()
            l2 = Category.objects.filter(
                parent=locks, name='Замки підвищеного захисту'
            ).first()
            if l2 is not None:
                return _nearest_menu_category(l2, _allowed_ids()) or l2
    name = (product.name or '').lower()
    brand = (product.brand or '').strip()
    if brand:
        root = Category.objects.filter(
            name=brand, parent__isnull=True, is_active=True
        ).first()
        if root is not None:
            sub = (
                Category.objects.filter(
                    parent=root, show_in_menu=True, is_active=True
                )
                .order_by('sort_order')
                .first()
            )
            return sub or root
    root_name = 'Циліндри' if 'циліндр' in name else 'Замки'
    root = Category.objects.filter(name=root_name, parent__isnull=True).first()
    if root is None:
        return None
    return _nearest_menu_category(root, _allowed_ids()) or root


def _product_mech(product):
    for row in product.product_attributes.select_related(
        'attribute_value__attribute'
    ):
        attr = row.attribute_value.attribute
        if attr.slug == 'mech':
            return row.attribute_value.value
    return ''


def _is_cylinder_product(product):
    name = (product.name or '').lower()
    sku = (product.sku or '').upper()
    if sku.startswith('ABR-') or sku.startswith('HOME-'):
        return True
    if name.startswith('циліндр'):
        return True
    return False


def _size_ab(product):
    if product.size_a and product.size_b:
        return f'{product.size_a}×{product.size_b}'
    return ''


def _cylinder_target(product):
    from catalog.category_tree import resolve_leaf_category
    from catalog.models import Category

    cyl = Category.objects.filter(
        name='Циліндри', parent__isnull=True, is_active=True
    ).first()
    if cyl is None:
        return None
    mech = _product_mech(product) or 'Ключ-ключ'
    return resolve_leaf_category(cyl, mech, _size_ab(product)) or cyl


def repair_cylinder_products():
    from catalog.db_compat import product_qs

    moved = 0
    qs = product_qs().select_related('category').prefetch_related(
        'product_attributes__attribute_value__attribute'
    )
    for product in qs:
        if not _is_cylinder_product(product):
            continue
        target = _cylinder_target(product)
        if target is None or target.pk == product.category_id:
            continue
        product.category_id = target.pk
        product.save(update_fields=['category'])
        moved += 1
    return moved


def reassign_products_to_menu():
    from catalog.db_compat import product_qs

    allowed = _allowed_ids()
    moved = 0
    if allowed:
        qs = product_qs().select_related('category')
        for product in qs:
            if _is_cylinder_product(product):
                continue
            cat = product.category
            if cat is not None and cat.pk in allowed:
                continue
            target = None
            if cat is not None:
                target = _nearest_menu_category(cat, allowed)
            if target is None:
                target = _fallback_category(product)
            if target is None or target.pk == product.category_id:
                continue
            product.category_id = target.pk
            product.save(update_fields=['category'])
            moved += 1
    moved += repair_cylinder_products()
    return moved


def sync_category_tree():
    for old_name, new_name in ROOT_ALIASES.items():
        _rename_root(old_name, new_name)

    keep_names = [item['name'] for item in MENU_TREE]
    for name in keep_names:
        _dedupe_named_roots(name)

    roots = {}
    for index, item in enumerate(MENU_TREE, start=1):
        root = _get_or_create_root(item, index)
        roots[item['name']] = root
        for old_name, new_name in (
            (old, new) for parent, old, new in CHILD_ALIASES if parent == item['name']
        ):
            _rename_child(root, old_name, new_name)
        for sub_i, (sub_name, leaves) in enumerate(item['tree'].items(), start=1):
            sub = _get_or_create_child(root, sub_name, sub_i)
            if item.get('logo') and item['name'] == 'Циліндри':
                _attach_logo(sub, item['logo'])
            for leaf_i, leaf_name in enumerate(leaves, start=1):
                _get_or_create_child(sub, leaf_name, leaf_i)
        _hide_stale_children(root, item['tree'])

    _hide_extra_roots(keep_names)
    return roots
