from urllib.parse import parse_qs, urlencode, urlparse

from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from unfold.views import ChangeList

from .filter_sort import next_sort_order
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


def build_filter_nav_context(attribute_id='', group_id='', hide_add=False):
    crumbs = [{'title': 'Фільтри', 'url': _hub_url()}]
    selected_group = None
    selected_attr = None
    items = []
    level = 'groups'
    add_url = _with_next(reverse('admin:catalog_attributegroup_add'), _hub_url())
    add_label = 'Додати групу'

    if group_id == NONE_GROUP:
        selected_group = None
        ungrouped = True
    elif group_id.isdigit():
        ungrouped = False
        selected_group = AttributeGroup.objects.filter(pk=int(group_id)).first()
    else:
        ungrouped = False

    if group_id and (selected_group is not None or ungrouped):
        level = 'filters'
        group_title = selected_group.name if selected_group else 'Без групи'
        crumbs.append({'title': group_title, 'url': _group_url(group_id)})
        attr_qs = Attribute.objects.filter(group=selected_group).annotate(
            value_count=Count('values')
        )
        items = []
        for attr in attr_qs:
            edit = reverse('admin:catalog_attribute_change', args=[attr.pk])
            items.append(
                {
                    'name': attr.name,
                    'meta': f'{attr.value_count} знач.',
                    'url': _attribute_url(group_id, attr.pk),
                    'edit_url': _with_next(edit, _group_url(group_id)),
                }
            )
        add_params = {'next': _group_url(group_id)}
        if selected_group is not None:
            add_params['group'] = str(selected_group.pk)
        add_url = f'{reverse("admin:catalog_attribute_add")}?{urlencode(add_params)}'
        add_label = 'Додати фільтр'

    if attribute_id.isdigit():
        selected_attr = (
            Attribute.objects.select_related('group').filter(pk=int(attribute_id)).first()
        )
        if selected_attr:
            level = 'values'
            gkey = _group_key(selected_attr.group)
            if not group_id:
                crumbs.append(
                    {
                        'title': selected_attr.group.name
                        if selected_attr.group
                        else 'Без групи',
                        'url': _group_url(gkey),
                    }
                )
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

    if level == 'groups':
        groups = AttributeGroup.objects.annotate(
            attr_count=Count('attributes', distinct=True),
            value_count=Count('attributes__values', distinct=True),
        )
        items = []
        for group in groups:
            edit = reverse('admin:catalog_attributegroup_change', args=[group.pk])
            items.append(
                {
                    'name': group.name,
                    'meta': f'{group.attr_count} фільтрів · {group.value_count} знач.',
                    'url': _group_url(group.pk),
                    'edit_url': _with_next(edit, _hub_url()),
                }
            )
        none_count = Attribute.objects.filter(group__isnull=True).count()
        if none_count:
            none_values = AttributeValue.objects.filter(
                attribute__group__isnull=True
            ).count()
            items.append(
                {
                    'name': 'Без групи',
                    'meta': f'{none_count} фільтрів · {none_values} знач.',
                    'url': _group_url(NONE_GROUP),
                    'edit_url': '',
                }
            )

    title = crumbs[-1]['title'] if crumbs else 'Фільтри'
    hint = {
        'groups': 'Оберіть групу або додайте нову.',
        'filters': 'Оберіть фільтр або додайте новий у цю групу.',
        'values': 'Редагуйте значення, додайте або видаліть.',
    }[level]
    empty = ''
    if level == 'values':
        empty = 'У цього фільтра ще немає значень.'
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
    """Рівні 1–2: групи та фільтри в «Фільтри»."""

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

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        group_id = (request.GET.get('group') or '').strip()
        if group_id.isdigit():
            initial['group'] = int(group_id)
            siblings = Attribute.objects.filter(group_id=int(group_id))
        else:
            siblings = Attribute.objects.filter(group__isnull=True)
        initial['sort_order'] = next_sort_order(siblings)
        return initial


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
            return ('value', 'slug', 'sort_order')
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
            siblings = AttributeValue.objects.filter(attribute_id=int(attribute_id))
        else:
            siblings = AttributeValue.objects.none()
        initial['sort_order'] = next_sort_order(siblings)
        return initial
