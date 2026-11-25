"""Ступінчастий вибір батьківської категорії: корінь → дитина → онук."""

from django.forms.widgets import Widget

from .models import Category


def build_parent_cascade_tree(exclude_pk=None):
    rows = list(
        Category.objects.order_by('sort_order', 'name').only(
            'id', 'name', 'parent_id'
        )
    )
    skip = set()
    if exclude_pk:
        skip.add(int(exclude_pk))
        by_parent = {}
        for cat in rows:
            by_parent.setdefault(cat.parent_id, []).append(cat)
        stack = list(by_parent.get(int(exclude_pk), []))
        while stack:
            node = stack.pop()
            skip.add(node.pk)
            stack.extend(by_parent.get(node.pk, []))

    children = {}
    for cat in rows:
        if cat.pk in skip:
            continue
        children.setdefault(cat.parent_id, []).append(cat)

    def pack(parent_id):
        packed = []
        for cat in children.get(parent_id, []):
            packed.append(
                {
                    'id': cat.pk,
                    'name': cat.name,
                    'children': pack(cat.pk),
                }
            )
        return packed

    return pack(None)


class CategoryParentCascadeWidget(Widget):
    template_name = 'admin/catalog/parent_cascade.html'

    class Media:
        css = {'all': ('css/admin/category_parent_cascade.css',)}
        js = ('js/admin/category_parent_cascade.js',)

    def __init__(self, attrs=None, tree=None, allow_empty=True):
        super().__init__(attrs)
        self.tree = tree if tree is not None else []
        self.allow_empty = allow_empty

    def format_value(self, value):
        if value in (None, ''):
            return ''
        if hasattr(value, 'pk'):
            return str(value.pk)
        return str(value)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context['widget']
        field_id = widget['attrs'].get('id') or f'id_{name}'
        widget['attrs']['id'] = field_id
        widget['tree_json'] = self.tree
        widget['tree_id'] = f'{field_id}_tree'
        widget['value'] = self.format_value(value)
        widget['name'] = name
        widget['allow_empty'] = self.allow_empty
        return context
