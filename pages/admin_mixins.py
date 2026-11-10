"""Спільні міксини адмінки Unfold."""

from __future__ import annotations

from django.db import models
from django.http import HttpResponseRedirect

from .admin_filters import (
    ZamkyAllValuesDropdownFilter,
    ZamkyBooleanDropdownFilter,
    ZamkyChoicesDropdownFilter,
    ZamkyRangeDateFilter,
    ZamkyRelatedDropdownFilter,
)


class TopDropdownFiltersMixin:
    """
    Усі list_filter — випадаючі меню зверху сторінки (не сайдбар справа).
    Підписи без префікса «За».
    """

    list_filter_sheet = False

    def get_list_filter(self, request):
        raw = list(super().get_list_filter(request))
        converted = []
        options: dict = {}

        for item in raw:
            if isinstance(item, (tuple, list)):
                field_path, filter_cls = item[0], item[1]
                converted.append((field_path, filter_cls))
                options[field_path] = {
                    'horizontal': True,
                    'label': self._filter_label_for_path(field_path),
                }
                continue

            if isinstance(item, str):
                field_path = item
                field = self._resolve_field(field_path)
                filter_cls = self._dropdown_class_for_field(field)
                converted.append((field_path, filter_cls))
                options[field_path] = {
                    'horizontal': True,
                    'label': self._filter_label_for_path(field_path),
                }
                continue

            converted.append(item)
            param = getattr(item, 'parameter_name', None)
            title = getattr(item, 'title', param)
            if param:
                options[param] = {
                    'horizontal': True,
                    'label': str(title).strip() if title else param,
                }

        self._zamky_list_filter_options = options
        return converted

    @property
    def list_filter_options(self):
        if hasattr(self, '_zamky_list_filter_options'):
            return self._zamky_list_filter_options
        return {}

    def _resolve_field(self, field_path: str):
        bits = field_path.split('__')
        field = None
        model = self.model
        for bit in bits:
            field = model._meta.get_field(bit)
            model = getattr(getattr(field, 'remote_field', None), 'model', model)
        return field

    def _filter_label_for_path(self, field_path: str) -> str:
        try:
            return str(self._resolve_field(field_path).verbose_name).strip()
        except Exception:
            return field_path

    @staticmethod
    def _dropdown_class_for_field(field):
        if getattr(field, 'remote_field', None) is not None:
            return ZamkyRelatedDropdownFilter
        if isinstance(field, models.BooleanField):
            return ZamkyBooleanDropdownFilter
        if isinstance(field, (models.DateTimeField, models.DateField)):
            return ZamkyRangeDateFilter
        if getattr(field, 'choices', None):
            return ZamkyChoicesDropdownFilter
        return ZamkyAllValuesDropdownFilter


class DefaultActiveTrueFilterMixin:
    """Дефолт changelist: Активний = Так (якщо параметр ще не передано)."""

    default_active_param = 'is_active__exact'
    default_active_value = '1'

    def changelist_view(self, request, extra_context=None):
        if self.default_active_param not in request.GET:
            params = request.GET.copy()
            params[self.default_active_param] = self.default_active_value
            return HttpResponseRedirect(f'{request.path}?{params.urlencode()}')
        return super().changelist_view(request, extra_context)
