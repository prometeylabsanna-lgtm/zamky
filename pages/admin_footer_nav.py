"""Formset посилань підвалу для CMS «Підвал»."""

from __future__ import annotations

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from unfold.widgets import UnfoldBooleanWidget

from pages.admin_header_nav import CmsAdminNumberWidget
from pages.admin_site_content_widgets import CmsAdminTextInputWidget
from pages.footer_nav import FOOTER_NAV_GROUPS, ensure_default_footer_nav, footer_nav_queryset
from pages.models_footer import FooterNavLink
from pages.slug_utils import ensure_unique_slug


class FooterNavLinkForm(forms.ModelForm):
    class Meta:
        model = FooterNavLink
        fields = ("key", "group", "name", "name_ru", "url", "sort_order", "is_active")
        widgets = {
            "key": forms.HiddenInput(),
            "group": forms.HiddenInput(),
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
        self.fields["group"].required = False
        self.fields["name"].label = "Назва"
        self.fields["name_ru"].label = "Назва (RU)"
        self.fields["url"].label = "Посилання"
        self.fields["sort_order"].label = "Порядок"
        self.fields["is_active"].label = "Показувати"

    def group_code(self) -> str:
        raw = self["group"].value()
        return (raw or FooterNavLink.Group.CATALOG).strip()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("DELETE"):
            return cleaned
        name = (cleaned.get("name") or "").strip()
        url = (cleaned.get("url") or "").strip()
        group = (cleaned.get("group") or FooterNavLink.Group.CATALOG).strip()
        if not name and not url:
            return cleaned
        if not name:
            self.add_error("name", "Вкажіть назву.")
        if group != FooterNavLink.Group.ACTION and not url:
            self.add_error("url", "Вкажіть посилання.")
        return cleaned


class FooterNavLinkBaseFormSet(BaseModelFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        delete = form.fields.get("DELETE")
        if delete is not None:
            delete.widget = UnfoldBooleanWidget()
            delete.label = "Видалити"

    def grouped_forms(self):
        buckets = {key: [] for key, _ in FOOTER_NAV_GROUPS}
        for form in self.forms:
            buckets.setdefault(form.group_code(), []).append(form)
        return [
            {"key": key, "title": title, "forms": buckets.get(key, [])}
            for key, title in FOOTER_NAV_GROUPS
        ]

    def save(self, commit=True):
        super().save(commit=False)
        for obj in self.deleted_objects:
            obj.delete()
        saved = []
        counters: dict[str, int] = {}
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            name = (form.cleaned_data.get("name") or "").strip()
            if not name:
                continue
            obj = form.save(commit=False)
            obj.name = name
            obj.url = (form.cleaned_data.get("url") or "").strip()
            obj.group = (
                form.cleaned_data.get("group") or FooterNavLink.Group.CATALOG
            ).strip()
            if not (obj.key or "").strip():
                obj.key = ensure_unique_slug(
                    FooterNavLink,
                    f"{obj.group}-{name}",
                    instance_pk=obj.pk,
                    field="key",
                    fallback="footer",
                )
            order = form.cleaned_data.get("sort_order")
            if order is None:
                counters[obj.group] = counters.get(obj.group, 0)
                obj.sort_order = counters[obj.group]
            else:
                obj.sort_order = int(order)
            counters[obj.group] = max(counters.get(obj.group, 0), obj.sort_order + 1)
            if commit:
                obj.save()
            saved.append(obj)
        if commit:
            self.save_m2m()
        return saved


def build_footer_nav_formset(data=None):
    ensure_default_footer_nav()
    formset = modelformset_factory(
        FooterNavLink,
        form=FooterNavLinkForm,
        formset=FooterNavLinkBaseFormSet,
        extra=0,
        can_delete=True,
    )
    return formset(data=data, queryset=footer_nav_queryset(), prefix="footer_nav")
