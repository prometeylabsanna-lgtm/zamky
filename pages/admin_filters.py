"""Dropdown- та date-фільтри Unfold без префікса «За»."""

from collections.abc import Iterator

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.validators import EMPTY_VALUES
from django.db.models import DateTimeField, QuerySet
from django.forms import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from unfold.contrib.filters.admin.datetime_filters import RangeDateFilter
from unfold.contrib.filters.admin.mixins import DropdownMixin, ValueMixin
from unfold.contrib.filters.forms import DropdownForm
from unfold.utils import parse_date_str

from .admin_filter_forms import ZamkyRangeDateForm


def _filter_label(title) -> str:
    return str(title).strip()


class ZamkyRangeDateFilter(RangeDateFilter):
    """Компактний діапазон дат (і для DateTimeField) з українськими placeholder."""

    form_class = ZamkyRangeDateForm
    template = 'unfold/filters/filters_date_range.html'

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        filters = {}
        value_from = self.used_parameters.get(f'{self.parameter_name}_from')
        value_to = self.used_parameters.get(f'{self.parameter_name}_to')

        if isinstance(self.field, DateTimeField):
            if value_from not in EMPTY_VALUES and isinstance(value_from, str):
                filters[f'{self.parameter_name}__date__gte'] = parse_date_str(value_from)
            if value_to not in EMPTY_VALUES and isinstance(value_to, str):
                filters[f'{self.parameter_name}__date__lte'] = parse_date_str(value_to)
        else:
            if value_from not in EMPTY_VALUES and isinstance(value_from, str):
                filters[f'{self.parameter_name}__gte'] = parse_date_str(value_from)
            if value_to not in EMPTY_VALUES and isinstance(value_to, str):
                filters[f'{self.parameter_name}__lte'] = parse_date_str(value_to)

        try:
            return queryset.filter(**filters) if filters else queryset
        except (ValueError, ValidationError):
            return None


class ZamkyChoicesDropdownFilter(ValueMixin, DropdownMixin, admin.ChoicesFieldListFilter):
    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        if self.value() not in EMPTY_VALUES:
            return super().queryset(request, queryset)
        return queryset

    def choices(self, changelist: ChangeList) -> Iterator:
        choices = [self.all_option] if self.all_option else []
        choices.extend(self.field.flatchoices)
        yield {
            'form': self.form_class(
                label=_filter_label(self.title),
                name=self.lookup_kwarg,
                choices=choices,
                data={self.lookup_kwarg: self.value()},
            ),
        }


class ZamkyRelatedDropdownFilter(ValueMixin, DropdownMixin, admin.RelatedFieldListFilter):
    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        if self.value() not in EMPTY_VALUES:
            return super().queryset(request, queryset)
        return queryset

    def choices(self, changelist: ChangeList) -> Iterator:
        choices = (
            [self.all_option, *self.lookup_choices]
            if self.all_option
            else list(self.lookup_choices)
        )
        yield {
            'form': self.form_class(
                label=_filter_label(self.title),
                name=self.lookup_kwarg,
                choices=choices,
                data={self.lookup_kwarg: self.value()},
            ),
        }


class ZamkyAllValuesDropdownFilter(ValueMixin, DropdownMixin, admin.AllValuesFieldListFilter):
    def choices(self, changelist: ChangeList) -> Iterator:
        choices = [self.all_option] if self.all_option else []
        for val in self.lookup_choices:
            if val is None:
                continue
            choices.append((str(val), str(val)))
        yield {
            'form': self.form_class(
                label=_filter_label(self.title),
                name=self.lookup_kwarg,
                choices=choices,
                data={self.lookup_kwarg: self.value()},
            ),
        }


class ZamkyBooleanDropdownFilter(ValueMixin, DropdownMixin, admin.BooleanFieldListFilter):
    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        if self.value() not in EMPTY_VALUES:
            return super().queryset(request, queryset)
        return queryset

    def choices(self, changelist: ChangeList) -> Iterator:
        choices = [
            self.all_option,
            ('1', _('Yes')),
            ('0', _('No')),
        ]
        yield {
            'form': DropdownForm(
                label=_filter_label(self.title),
                name=self.lookup_kwarg,
                choices=choices,
                data={self.lookup_kwarg: self.value()},
            ),
        }
