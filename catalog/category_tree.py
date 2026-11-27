"""Дерево категорій: меню, нащадки, сід з макета."""

from django.db.models import Prefetch

MENU_MAX_DEPTH = 2

TYPE_ROOT_NAMES = (
    'Замки',
    'Циліндри',
    'Дверна фурнітура',
    'Броненакладки',
    'Дотягувачі',
    'Контроль доступу',
)
BRAND_ROOT_NAMES = ('Mottura', 'Cisa', 'Elbor', 'Apecs', 'Securame', 'Kale')
BRAND_TYPE_SUBS = ('Замки', 'Циліндри', 'Броненакладки')

_BRAND_SUB = {
    'Замки': [],
    'Циліндри': [],
    'Броненакладки': [],
}

MENU_TREE = [
    {
        'name': 'Замки',
        'name_ru': 'Замки',
        'lock': 'pad',
        'logo': 'menu/p2_8.png',
        'home_subtitle': 'Врізні, накладні, електромеханічні',
        'tree': {
            'Врізні замки': [
                'Циліндрові врізні замки',
                'Сувальдні врізні замки',
                'Магнітні врізні замки',
                'Електромеханічні врізні замки',
                'Інші врізні замки',
            ],
            'Накладні замки': [
                'Циліндрові накладні замки',
                'Сувальдні накладні замки',
                'Електромеханічні накладні замки',
            ],
            'Сувальдні замки': [
                'Сувальдні врізні замки',
                'Сувальдні накладні замки',
            ],
            'Замки підвищеного захисту': [
                'Багатоточкові замки',
                'Замки для броньованих дверей',
            ],
        },
    },
    {
        'name': 'Циліндри',
        'name_ru': 'Цилиндры',
        'lock': 'cyl',
        'logo': 'menu/p2_9.png',
        'home_subtitle': 'Секретність та надійність',
        'tree': {
            'Ключ-ключ': ['Стандартні', 'Підвищеної секретності'],
            'Ключ-вертушка': ['Стандартні', 'Підвищеної секретності'],
            'Половинчасті циліндри': [],
            'Циліндри підвищеної секретності': [],
        },
    },
    {
        'name': 'Дверна фурнітура',
        'name_ru': 'Дверная фурнитура',
        'logo': 'menu/p2_10.png',
        'home_subtitle': 'Ручки, петлі, завіси і розетки',
        'tree': {
            'Ручки': ['Ручки на розетці', 'Ручки на планці', 'Ручки-скоби'],
            'Петлі': ['Врізні петлі', 'Накладні петлі', 'Приховані петлі'],
            'Завіси': [],
            'Розетки': [],
            'Упори': [],
        },
    },
    {
        'name': 'Броненакладки',
        'name_ru': 'Броненакладки',
        'logo': 'menu/p2_11.png',
        'home_subtitle': 'Захист від злому',
        'tree': {
            'Накладні броненакладки': [],
            'Врізні броненакладки': [],
            'З захистом циліндра': [],
        },
    },
    {
        'name': 'Дотягувачі',
        'name_ru': 'Доводчики',
        'logo': 'menu/p2_12.png',
        'home_subtitle': 'Для комфортного закривання',
        'tree': {
            'Верхні дотягувачі': [],
            'Підлогові дотягувачі': [],
            'Приховані дотягувачі': [],
        },
    },
    {
        'name': 'Контроль доступу',
        'name_ru': 'Контроль доступа',
        'logo': 'menu/p2_13.png',
        'home_subtitle': 'Кодові замки, домофони, СКУД',
        'tree': {
            'Кодові замки': [],
            'Домофони': [],
            'СКУД': [],
            'Електромагнітні замки': [],
        },
    },
    {'name': 'Mottura', 'logo': 'mottura.png', 'tree': dict(_BRAND_SUB)},
    {'name': 'Cisa', 'logo': 'cisa.png', 'tree': dict(_BRAND_SUB)},
    {'name': 'Elbor', 'logo': 'elbor.png', 'tree': dict(_BRAND_SUB)},
    {'name': 'Apecs', 'logo': 'apecs.png', 'tree': dict(_BRAND_SUB)},
    {'name': 'Securame', 'logo': 'securame.png', 'tree': dict(_BRAND_SUB)},
    {'name': 'Kale', 'logo': 'kale.png', 'tree': dict(_BRAND_SUB)},
]

ROOT_ALIASES = {
    'Серцевини (циліндри)': 'Циліндри',
}

CHILD_ALIASES = (
    ('Циліндри', 'Ключ / ключ', 'Ключ-ключ'),
    ('Циліндри', 'Ключ / тумблер', 'Ключ-вертушка'),
    ('Циліндри', 'Половинчастий', 'Половинчасті циліндри'),
    ('Замки', 'Врізні', 'Врізні замки'),
    ('Замки', 'Накладні', 'Накладні замки'),
)

MECH_ALIASES = {
    'Ключ / ключ': 'Ключ-ключ',
    'Ключ-ключ': 'Ключ-ключ',
    'Ключ / тумблер': 'Ключ-вертушка',
    'Ключ-вертушка': 'Ключ-вертушка',
    'Половинчастий': 'Половинчасті циліндри',
    'Половинчасті циліндри': 'Половинчасті циліндри',
}


def category_depth(category):
    depth = 0
    seen = set()
    node = category.parent if category is not None else None
    while node is not None and node.pk not in seen:
        seen.add(node.pk)
        depth += 1
        node = node.parent
    return depth


def subtree_ids(root_id):
    from catalog.models import Category

    by_parent = {}
    for pk, parent_id in Category.objects.values_list('pk', 'parent_id'):
        by_parent.setdefault(parent_id, []).append(pk)
    out = []
    stack = [root_id]
    while stack:
        current = stack.pop()
        out.append(current)
        stack.extend(by_parent.get(current, []))
    return out


CORE_COLOR_ROOT = 'Циліндри'


def cylinder_category_ids():
    from catalog.models import Category

    ids = []
    for root in Category.objects.filter(name=CORE_COLOR_ROOT):
        ids.extend(subtree_ids(root.pk))
    return frozenset(ids)


def product_needs_core_color(product):
    if product is None:
        return False
    if (getattr(product, 'color_code', None) or '').strip():
        return True
    category = getattr(product, 'category', None)
    if category is None:
        return False
    return category.pk in cylinder_category_ids()


def category_path_label(category):
    names = [category.name]
    seen = set()
    node = category.parent
    while node is not None and node.pk not in seen:
        seen.add(node.pk)
        names.append(node.name)
        node = node.parent
    return ' / '.join(reversed(names))


def category_logo_url(category):
    logo = getattr(category, 'logo', None)
    if not logo:
        return ''
    try:
        return logo.url or ''
    except ValueError:
        return ''


def _menu_children_qs():
    from catalog.models import Category

    return Category.objects.filter(is_active=True, show_in_menu=True).order_by(
        'sort_order', 'name'
    )


def menu_payload():
    from catalog.models import Category

    leaves_qs = _menu_children_qs()
    subs_qs = _menu_children_qs().prefetch_related(
        Prefetch('children', queryset=leaves_qs)
    )
    roots = (
        Category.objects.filter(
            is_active=True, show_in_menu=True, parent__isnull=True
        )
        .prefetch_related(Prefetch('children', queryset=subs_qs))
        .order_by('sort_order', 'name')
    )
    rows = []
    for root in roots:
        icon = (root.icon or '').strip()
        lock = icon if icon in {'cyl', 'pad', 'shield'} else ''
        rows.append(
            {
                'name': root.card_name(),
                'url': root.get_absolute_url(),
                'lock': lock,
                'logo_url': category_logo_url(root),
                'subs': [
                    {
                        'name': sub.card_name(),
                        'url': sub.get_absolute_url(),
                        'logo_url': category_logo_url(sub),
                        'leaves': [
                            {
                                'name': leaf.card_name(),
                                'url': leaf.get_absolute_url(),
                            }
                            for leaf in sub.children.all()
                        ],
                    }
                    for sub in root.children.all()
                ],
            }
        )
    return rows


def ensure_category_tree():
    from catalog.menu_align import sync_category_tree

    return sync_category_tree()


def _match_named_child(parent, label):
    if parent is None or not label:
        return None
    kids = list(parent.children.filter(is_active=True))
    wanted = MECH_ALIASES.get(label, label)
    for child in kids:
        if child.name == wanted or child.name == label:
            return child
    needle = wanted.replace(' ', '').replace('-', '').lower()[:12]
    if not needle:
        return None
    for child in kids:
        compact = child.name.replace(' ', '').replace('-', '').lower()
        if needle in compact or compact.startswith(needle[:8]):
            return child
    return None


def resolve_leaf_category(root_or_cat, mech_label, size_ab):
    if root_or_cat is None:
        return None
    root = root_or_cat
    seen = set()
    while root.parent_id and root.pk not in seen:
        seen.add(root.pk)
        root = root.parent
    l2 = _match_named_child(root, mech_label)
    if l2 is None:
        return None
    kids = list(l2.children.filter(is_active=True, show_in_menu=True))
    if not kids:
        kids = list(l2.children.filter(is_active=True))
    if size_ab:
        for child in kids:
            if size_ab in child.name:
                return child
    std = next((child for child in kids if child.name == 'Стандартні'), None)
    if std is not None:
        return std
    if kids:
        return kids[0]
    return l2
