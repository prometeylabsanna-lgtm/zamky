"""Formset товарів «Популярні» для CMS головної."""

from __future__ import annotations

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldBooleanWidget

from catalog.models import Product
from pages.admin_header_nav import CmsAdminNumberWidget
from pages.models_popular import HomePopularProduct
from pages.popular_products import (
    POPULAR_TABS,
    ensure_default_popular,
    mark_popular_lists_ready,
    popular_queryset,
)


class HomePopularProductForm(forms.ModelForm):
    class Meta:
        model = HomePopularProduct
        fields = ("tab", "product", "sort_order", "is_active")
        widgets = {
            "tab": forms.HiddenInput(),
            "product": UnfoldAdminSelectWidget(),
            "sort_order": CmsAdminNumberWidget(),
            "is_active": UnfoldBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["product"]
        field.required = False
        field.empty_label = "— оберіть товар —"
        field.queryset = Product.objects.order_by("name", "sku")
        field.label = "Товар"
        field.label_from_instance = lambda obj: (
            f"{obj.name} · {obj.sku}" if obj.sku else obj.name
        )
        self.fields["sort_order"].required = False
        self.fields["is_active"].required = False
        self.fields["tab"].required = False
        self.fields["sort_order"].label = "Порядок"
        self.fields["is_active"].label = "Показувати"

    def tab_code(self) -> str:
        raw = self["tab"].value()
        return (raw or HomePopularProduct.Tab.HITS).strip()

    def validate_unique(self):
        return

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("DELETE"):
            return cleaned
        product = cleaned.get("product")
        tab = (cleaned.get("tab") or HomePopularProduct.Tab.HITS).strip()
        if not product:
            return cleaned
        cleaned["tab"] = tab
        return cleaned


class HomePopularProductBaseFormSet(BaseModelFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        delete = form.fields.get("DELETE")
        if delete is not None:
            delete.widget = UnfoldBooleanWidget()
            delete.label = "Видалити"

    def grouped_forms(self):
        buckets = {key: [] for key, _ in POPULAR_TABS}
        for form in self.forms:
            buckets.setdefault(form.tab_code(), []).append(form)
        return [
            {"key": key, "title": title, "forms": buckets.get(key, [])}
            for key, title in POPULAR_TABS
        ]

    def clean(self):
        super().clean()
        seen: set[tuple[str, int]] = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            product = form.cleaned_data.get("product")
            tab = (form.cleaned_data.get("tab") or "").strip()
            if not product:
                continue
            key = (tab, product.pk)
            if key in seen:
                form.add_error("product", "Цей товар уже є в цій вкладці.")
            seen.add(key)

    def save(self, commit=True):
        super().save(commit=False)
        for obj in self.deleted_objects:
            obj.delete()
        saved = []
        counters: dict[str, int] = {}
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            product = form.cleaned_data.get("product")
            if not product:
                continue
            obj = form.save(commit=False)
            obj.product = product
            obj.tab = (
                form.cleaned_data.get("tab") or HomePopularProduct.Tab.HITS
            ).strip()
            order = form.cleaned_data.get("sort_order")
            if order is None:
                counters[obj.tab] = counters.get(obj.tab, 0)
                obj.sort_order = counters[obj.tab]
            else:
                obj.sort_order = int(order)
            counters[obj.tab] = max(counters.get(obj.tab, 0), obj.sort_order + 1)
            if commit:
                obj.save()
            saved.append(obj)
        if commit:
            self.save_m2m()
            mark_popular_lists_ready()
        return saved


def build_popular_formset(data=None):
    ensure_default_popular()
    formset = modelformset_factory(
        HomePopularProduct,
        form=HomePopularProductForm,
        formset=HomePopularProductBaseFormSet,
        extra=0,
        can_delete=True,
    )
    return formset(data=data, queryset=popular_queryset(), prefix="popular")
