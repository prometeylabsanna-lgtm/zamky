from urllib.parse import urlencode, urlparse

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from .admin_parent_cascade import (
    CategoryParentCascadeWidget,
    build_parent_cascade_tree,
)
from .category_tree import (
    MENU_MAX_DEPTH,
    category_depth,
    category_logo_url,
    subtree_ids,
)
from .filter_sort import next_sort_order
from .models import Category, Product

ICON_CHOICES = (
    ('', '— логотип файлом'),
    ('cyl', 'Циліндр'),
    ('pad', 'Навісний замок'),
    ('shield', 'Щит'),
)
LOCK_ICONS = {'cyl', 'pad', 'shield'}

HUB_NAME = 'admin:catalog_category_changelist'


def _hub_url():
    return reverse(HUB_NAME)


def _children_url(parent_id):
    return f'{_hub_url()}?parent={parent_id}'


def _safe_next(request):
    raw = (request.POST.get('next') or request.GET.get('next') or '').strip()
    if not raw.startswith('/'):
        return ''
    path = urlparse(raw).path
    if '/catalog/category/' in path:
        return raw
    return ''


def _with_next(url, next_url):
    sep = '&' if '?' in url else '?'
    return f'{url}{sep}{urlencode({"next": next_url})}'


def build_category_nav_context(parent_id=''):
    crumbs = [{'title': 'Категорії', 'url': _hub_url()}]
    parent = None
    if parent_id.isdigit():
        parent = Category.objects.filter(pk=int(parent_id)).first()
        if parent is None:
            parent_id = ''

    if parent is not None:
        chain = []
        node = parent
        seen = set()
        while node is not None and node.pk not in seen:
            seen.add(node.pk)
            chain.append(node)
            node = node.parent
        for cat in reversed(chain):
            crumbs.append(
                {
                    'title': cat.name,
                    'url': _children_url(cat.pk),
                }
            )

    if parent is None:
        qs = Category.objects.filter(parent__isnull=True)
        add_parent = ''
        item_depth = 0
        hint = 'Іконка ліворуч — змінити лого. Назва — підкатегорії.'
    else:
        qs = Category.objects.filter(parent=parent)
        add_parent = str(parent.pk)
        item_depth = category_depth(parent) + 1
        hint = 'Підкатегорії цього рівня. Клік — глибше, «Змінити» — картка.'

    qs = qs.annotate(child_count=Count('children')).order_by('sort_order', 'name')
    can_drill = item_depth < MENU_MAX_DEPTH
    list_url = crumbs[-1]['url'] if crumbs[-1].get('url') else _hub_url()
    items = []
    for cat in qs:
        edit = _with_next(
            reverse('admin:catalog_category_change', args=[cat.pk]),
            list_url,
        )
        icon = (cat.icon or '').strip()
        items.append(
            {
                'name': cat.name,
                'meta': f'{cat.child_count} підкат.',
                'url': _children_url(cat.pk) if can_drill else edit,
                'edit_url': edit,
                'lock': icon if icon in LOCK_ICONS else '',
                'logo_url': category_logo_url(cat),
                'mark': True,
            }
        )

    add_url = ''
    add_label = ''
    if item_depth <= MENU_MAX_DEPTH:
        add_params = {'next': crumbs[-1]['url'] or _hub_url()}
        if add_parent:
            add_params['parent'] = add_parent
        add_url = f'{reverse("admin:catalog_category_add")}?{urlencode(add_params)}'
        add_label = 'Додати категорію'

    title = crumbs[-1]['title'] if crumbs else 'Категорії'
    return {
        'filter_nav_level': 'groups',
        'filter_nav_items': items,
        'filter_nav_crumbs': crumbs,
        'filter_nav_hint': hint,
        'filter_nav_title': title,
        'filter_nav_attribute': None,
        'filter_nav_add_url': add_url,
        'filter_nav_add_label': add_label,
        'title': title,
    }


class CategoryAdminForm(forms.ModelForm):
    icon = forms.ChoiceField(
        label='Іконка в меню',
        choices=ICON_CHOICES,
        required=False,
        help_text='Замочок у меню. Для бренду залиште порожнім і завантажте логотип.',
    )

    class Meta:
        model = Category
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if (self.instance.icon or '').strip() not in LOCK_ICONS:
            self.initial['icon'] = ''
        parent_field = self.fields['parent']
        parent_field.required = False
        parent_field.help_text = (
            'Як у каталозі: корінь, далі підкатегорія, далі онук. '
            '«Без батьківської» — перший рівень.'
        )
        parent_field.widget = CategoryParentCascadeWidget(
            tree=build_parent_cascade_tree(exclude_pk=self.instance.pk),
        )

    def clean_parent(self):
        parent = self.cleaned_data.get('parent')
        instance = self.instance
        if parent is None:
            return parent
        if instance.pk and parent.pk == instance.pk:
            raise ValidationError('Категорія не може бути батьківською для себе.')
        seen = set()
        if instance.pk:
            seen.add(instance.pk)
        node = parent
        while node is not None:
            if node.pk in seen:
                raise ValidationError(
                    'Категорія не може бути нащадком самої себе.'
                )
            seen.add(node.pk)
            node = node.parent
        if category_depth(parent) >= MENU_MAX_DEPTH:
            raise ValidationError('Меню підтримує щонайбільше 3 рівні.')
        return parent


class CategoryTreeReturnMixin:
    change_form_before_template = 'admin/catalog/filter_tree_next.html'

    def render_change_form(
        self, request, context, add=False, change=False, form_url='', obj=None
    ):
        context['filter_tree_next'] = _safe_next(request)
        return super().render_change_form(
            request, context, add=add, change=change, form_url=form_url, obj=obj
        )

    def response_post_save_add(self, request, obj):
        nxt = _safe_next(request)
        if nxt:
            return HttpResponseRedirect(nxt)
        return super().response_post_save_add(request, obj)

    def response_post_save_change(self, request, obj):
        nxt = _safe_next(request)
        if nxt:
            return HttpResponseRedirect(nxt)
        return super().response_post_save_change(request, obj)


def category_has_products(category):
    if category is None or not category.pk:
        return False
    return Product.objects.filter(category_id__in=subtree_ids(category.pk)).exists()


class CategoryTreeMixin:
    show_add_link = False

    def has_delete_permission(self, request, obj=None):
        if obj is not None and category_has_products(obj):
            return False
        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        if category_has_products(obj):
            messages.error(
                request,
                'Категорію не видалено: у ній або в підкатегоріях є товари. '
                'Спочатку перенесіть товари.',
            )
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        blocked = [obj.pk for obj in queryset if category_has_products(obj)]
        if blocked:
            messages.error(
                request,
                'Категорії з товарами не видалено. Спочатку перенесіть товари.',
            )
            queryset = queryset.exclude(pk__in=blocked)
        if queryset.exists():
            super().delete_queryset(request, queryset)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        parent_id = (request.GET.get('parent') or '').strip()
        if parent_id.isdigit() and not Category.objects.filter(pk=int(parent_id)).exists():
            return redirect(_hub_url())
        extra_context.update(build_category_nav_context(parent_id))
        context = {
            **self.admin_site.each_context(request),
            **extra_context,
            'opts': self.opts,
            'cl': None,
            'media': self.media,
            'has_add_permission': False,
            'is_popup': False,
        }
        return TemplateResponse(
            request, 'admin/catalog/filter_values_nav.html', context
        )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        parent = (request.GET.get('parent') or '').strip()
        if parent.isdigit():
            initial['parent'] = parent
            siblings = Category.objects.filter(parent_id=int(parent))
        else:
            siblings = Category.objects.filter(parent__isnull=True)
        initial['sort_order'] = next_sort_order(siblings)
        return initial
