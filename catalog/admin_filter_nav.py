from urllib.parse import parse_qs, urlencode, urlparse

from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from unfold.views import ChangeList

from .models import Attribute, AttributeGroup, AttributeValue

NONE_GROUP = 'none'
HUB_NAME = 'admin:catalog_attribute_changelist'
VALUES_NAME = 'admin:catalog_attributevalue_changelist'


def _hub_url():
    return reverse(HUB_NAME)


def _attribute_id_from_url(raw_url):
    if not raw_url:
        return ''
    return (parse_qs(urlparse(raw_url).query).get('attribute') or [''])[0].strip()


def bound_attribute_id(request, obj=None):
    if obj is not None and getattr(obj, 'attribute_id', None):
        return obj.attribute_id
    raw = (request.POST.get('attribute') or request.GET.get('attribute') or '').strip()
    if not raw:
        raw = _attribute_id_from_url(
            request.POST.get('next') or request.GET.get('next') or ''
        )
    if not raw:
        raw = _attribute_id_from_url(request.META.get('HTTP_REFERER') or '')
    if raw.isdigit() and Attribute.objects.filter(pk=int(raw)).exists():
        return int(raw)
    return None


def _values_list_url():
    return reverse(VALUES_NAME)


def _group_url(group_key):
    return f'{_hub_url()}?group={group_key}'


def _attribute_url(group_key, attribute_id):
    return f'{_values_list_url()}?group={group_key}&attribute={attribute_id}'


def _group_key(group):
    return str(group.pk) if group is not None else NONE_GROUP


def _safe_next(request):
    raw = (request.POST.get('next') or request.GET.get('next') or '').strip()
    if not raw.startswith('/'):
        return ''
    path = urlparse(raw).path
    allowed = (
        '/catalog/attribute/',
        '/catalog/attributegroup/',
        '/catalog/attributevalue/',
    )
    if any(chunk in path for chunk in allowed):
        return raw
    return ''


def _with_next(url, next_url):
    sep = '&' if '?' in url else '?'
    return f'{url}{sep}{urlencode({"next": next_url})}'


def _attribute_meta(attr):
    parts = [f'{attr.value_count} знач.']
    parts.append('фільтр у каталозі' if attr.filterable else 'лише в картці товару')
    return ' · '.join(parts)


def build_filter_nav_context(attribute_id='', group_id='', hide_add=False):
    """Два рівні: характеристики → значення. Групи — лише необовʼязкова позначка."""
    crumbs = [{'title': 'Характеристики', 'url': _hub_url()}]
    selected_attr = None
    level = 'filters'
    add_url = _with_next(reverse('admin:catalog_attribute_add'), _hub_url())
    add_label = 'Додати характеристику'

    if attribute_id.isdigit():
        selected_attr = (
            Attribute.objects.select_related('group').filter(pk=int(attribute_id)).first()
        )
        if selected_attr:
            level = 'values'
            gkey = _group_key(selected_attr.group)
            crumbs.append(
                {
                    'title': selected_attr.name,
                    'url': (
                        _attribute_url(gkey, selected_attr.pk) if hide_add else None
                    ),
                }
            )
            add_url = _with_next(
                f'{reverse("admin:catalog_attributevalue_add")}?attribute={selected_attr.pk}',
                _attribute_url(gkey, selected_attr.pk),
            )
            add_label = 'Додати значення'

    items = []
    if level == 'filters':
        attr_qs = (
            Attribute.objects.select_related('group')
            .annotate(value_count=Count('values'))
            .order_by('sort_order', 'name', 'pk')
        )
        for attr in attr_qs:
            gkey = _group_key(attr.group)
            edit = reverse('admin:catalog_attribute_change', args=[attr.pk])
            items.append(
                {
                    'name': attr.name,
                    'meta': _attribute_meta(attr),
                    'url': _attribute_url(gkey, attr.pk),
                    'edit_url': _with_next(edit, _hub_url()),
                }
            )

    title = crumbs[-1]['title'] if crumbs else 'Характеристики'
    hint = {
        'filters': (
            'Довідник характеристик товарів. Галочка «Показувати як фільтр у каталозі» '
            'додає характеристику в фільтри каталогу. Значення для товару можна '
            'вписати прямо в товарі — нові зʼявляться тут.'
        ),
        'values': 'Редагуйте значення, додайте або видаліть.',
    }[level]
    empty = ''
    if level == 'values':
        empty = 'У цієї характеристики ще немає значень.'
    if hide_add:
        add_url = ''
        add_label = ''
    return {
        'filter_nav_level': level,
        'filter_nav_items': items,
        'filter_nav_crumbs': crumbs,
        'filter_nav_hint': hint,
        'filter_nav_title': title,
        'filter_nav_attribute': selected_attr,
        'filter_nav_add_url': add_url,
        'filter_nav_add_label': add_label,
        'filter_nav_empty': empty,
        'title': title,
    }


class FilterTreeReturnMixin:
    change_form_before_template = 'admin/catalog/filter_tree_next.html'

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['filter_tree_next'] = _safe_next(request)
        attr_id = ''
        group_id = (request.GET.get('group') or '').strip()
        model = getattr(self, 'model', None)
        if model is AttributeValue:
            found = bound_attribute_id(request, obj)
            attr_id = str(found or '')
            if obj is not None and obj.attribute_id and obj.attribute.group_id:
                group_id = _group_key(obj.attribute.group)
        elif model is Attribute and obj is not None:
            group_id = _group_key(obj.group)
        elif model is AttributeGroup:
            group_id = ''
        context.update(
            build_filter_nav_context(attr_id, group_id, hide_add=True)
        )
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


class FilterValuesChangeList(ChangeList):
    def get_filters_params(self, params=None):
        lookup_params = super().get_filters_params(params)
        lookup_params.pop('group', None)
        lookup_params.pop('attribute', None)
        return lookup_params

    def get_filters(self, request):
        specs, has_filters, remaining, dup, active = super().get_filters(request)
        remaining.pop('group', None)
        remaining.pop('attribute', None)
        return specs, has_filters, remaining, dup, active


class FilterTreeMixin:
    """Рівень 1: список характеристик (групи не обовʼязкові)."""

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        attribute_id = (request.GET.get('attribute') or '').strip()
        group_id = (request.GET.get('group') or '').strip()
        if attribute_id.isdigit():
            attr = Attribute.objects.filter(pk=int(attribute_id)).select_related('group').first()
            if attr:
                return redirect(_attribute_url(_group_key(attr.group), attr.pk))
        extra_context.update(build_filter_nav_context(attribute_id, group_id))
        context = {
            **self.admin_site.each_context(request),
            **extra_context,
            'opts': self.opts,
            'cl': None,
            'media': self.media,
            'has_add_permission': False,
            'is_popup': False,
        }
        return TemplateResponse(request, 'admin/catalog/filter_values_nav.html', context)


class FilterValuesNavMixin:
    """Рівень 3: значення обраного фільтра."""

    list_before_template = 'admin/catalog/filter_values_crumbs.html'

    def get_changelist(self, request, **kwargs):
        return FilterValuesChangeList

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        attribute_id = (request.GET.get('attribute') or '').strip()
        group_id = (request.GET.get('group') or '').strip()
        if not attribute_id.isdigit():
            if group_id:
                return redirect(_group_url(group_id))
            return redirect(_hub_url())
        extra_context.update(build_filter_nav_context(attribute_id, group_id))
        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('attribute', 'attribute__group')
        attribute_id = (request.GET.get('attribute') or '').strip()
        if attribute_id.isdigit():
            return qs.filter(attribute_id=int(attribute_id))
        return qs.none()

    def get_list_display(self, request):
        if (request.GET.get('attribute') or '').strip():
            return ('value', 'slug')
        return self.list_display

    def get_list_filter(self, request):
        if (request.GET.get('attribute') or '').strip():
            return ()
        return super().get_list_filter(request)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        attribute_id = (request.GET.get('attribute') or '').strip()
        if attribute_id.isdigit():
            initial['attribute'] = int(attribute_id)
        return initial
