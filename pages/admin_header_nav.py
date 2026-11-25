"""Formset кнопок шапки для CMS «Шапка»."""

from __future__ import annotations

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from unfold.widgets import INPUT_CLASSES, UnfoldBooleanWidget

from pages.admin_site_content_widgets import CmsAdminTextInputWidget
from pages.header_nav import ensure_default_header_nav
from pages.models_header import HeaderNavLink
from pages.slug_utils import ensure_unique_slug


class CmsAdminNumberWidget(forms.NumberInput):
    def __init__(self, attrs=None):
        attrs = dict(attrs or {})
        existing = attrs.get("class", "")
        merged = list(INPUT_CLASSES)
        if existing:
            merged = list(dict.fromkeys([*merged, *existing.split()]))
        attrs["class"] = " ".join(merged)
        attrs.setdefault("min", "0")
        attrs.setdefault("step", "1")
        super().__init__(attrs=attrs)


class HeaderNavLinkForm(forms.ModelForm):
    class Meta:
        model = HeaderNavLink
        fields = ("key", "name", "name_ru", "url", "sort_order", "is_active")
        widgets = {
            "key": forms.HiddenInput(),
            "name": CmsAdminTextInputWidget(),
            "name_ru": CmsAdminTextInputWidget(),
            "url": CmsAdminTextInputWidget(),
            "sort_order": CmsAdminNumberWidget(),
            "is_active": UnfoldBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = False
        self.fields["name_ru"].required = False
        self.fields["url"].required = False
        self.fields["sort_order"].required = False
        self.fields["is_active"].required = False
        self.fields["key"].required = False
        self.fields["name"].label = "Назва"
        self.fields["name_ru"].label = "Назва (RU)"
        self.fields["url"].label = "Посилання"
        self.fields["sort_order"].label = "Порядок"
        self.fields["is_active"].label = "Показувати"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("DELETE"):
            return cleaned
        name = (cleaned.get("name") or "").strip()
        url = (cleaned.get("url") or "").strip()
        if not name and not url:
            return cleaned
        if not name:
            self.add_error("name", "Вкажіть назву.")
        if not url:
            self.add_error("url", "Вкажіть посилання.")
        return cleaned


class HeaderNavLinkBaseFormSet(BaseModelFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        delete = form.fields.get("DELETE")
        if delete is not None:
            delete.widget = UnfoldBooleanWidget()
            delete.label = "Видалити"

    def save(self, commit=True):
        super().save(commit=False)
        for obj in self.deleted_objects:
            obj.delete()
        saved = []
        for index, form in enumerate(self.forms):
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            name = (form.cleaned_data.get("name") or "").strip()
            url = (form.cleaned_data.get("url") or "").strip()
            if not name:
                continue
            obj = form.save(commit=False)
            obj.name = name
            obj.url = url
            if not (obj.key or "").strip():
                obj.key = ensure_unique_slug(
                    HeaderNavLink,
                    name,
                    instance_pk=obj.pk,
                    field="key",
                    fallback="nav",
                )
            order = form.cleaned_data.get("sort_order")
            obj.sort_order = index if order is None else int(order)
            if commit:
                obj.save()
            saved.append(obj)
        if commit:
            self.save_m2m()
        return saved


def build_header_nav_formset(data=None):
    ensure_default_header_nav()
    formset = modelformset_factory(
        HeaderNavLink,
        form=HeaderNavLinkForm,
        formset=HeaderNavLinkBaseFormSet,
        extra=0,
        can_delete=True,
    )
    queryset = HeaderNavLink.objects.all().order_by("sort_order", "pk")
    return formset(data=data, queryset=queryset, prefix="header_nav")
