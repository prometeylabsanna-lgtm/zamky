"""Форми CMS «Головна — Підбір»: двері та варіанти фільтрів."""

from __future__ import annotations

from django import forms
from django.db.models import Q
from django.forms import modelformset_factory
from unfold.widgets import INPUT_CLASSES, UnfoldAdminFileFieldWidget, UnfoldBooleanWidget

from catalog.models import Attribute, Category
from pages.admin_site_content_widgets import CmsAdminTextInputWidget
from pages.models_picker import PickerDoor, PickerFilter, PickerFilterOption
from pages.slug_utils import ensure_unique_slug


class PickerDoorForm(forms.ModelForm):
    class Meta:
        model = PickerDoor
        fields = (
            "label_line1",
            "label_line1_ru",
            "label_line2",
            "label_line2_ru",
            "image",
            "categories",
            "is_active",
        )
        widgets = {
            "label_line1": CmsAdminTextInputWidget(),
            "label_line1_ru": CmsAdminTextInputWidget(),
            "label_line2": CmsAdminTextInputWidget(),
            "label_line2_ru": CmsAdminTextInputWidget(),
            "image": UnfoldAdminFileFieldWidget(
                attrs={"accept": "image/png,image/jpeg,image/webp"}
            ),
            "categories": forms.CheckboxSelectMultiple(
                attrs={"class": "home-picker-admin-cats"}
            ),
            "is_active": UnfoldBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["label_line1"].label = "Рядок 1"
        self.fields["label_line1_ru"].label = "Рядок 1 (RU)"
        self.fields["label_line1_ru"].required = False
        self.fields["label_line2"].label = "Рядок 2"
        self.fields["label_line2"].required = False
        self.fields["label_line2_ru"].label = "Рядок 2 (RU)"
        self.fields["label_line2_ru"].required = False
        self.fields["image"].label = "Картинка"
        self.fields["image"].required = False
        from pages.admin_guidelines import IMAGE_HINTS

        self.fields["image"].help_text = IMAGE_HINTS["picker_door"]
        self.fields["categories"].label = "Категорії товарів"
        self.fields["categories"].required = False
        self.fields["categories"].queryset = Category.objects.filter(
            is_active=True
        ).order_by("sort_order", "name")
        self.fields["categories"].help_text = (
            "Товари з цих категорій (і вкладених) покаже підбір."
        )
        self.fields["is_active"].label = "Показувати на головній"
        self.fields["is_active"].required = False


class PickerFilterMetaForm(forms.ModelForm):
    class Meta:
        model = PickerFilter
        fields = ("attribute", "label", "label_ru", "is_active")
        widgets = {
            "attribute": forms.Select(attrs={"class": " ".join(INPUT_CLASSES)}),
            "label": CmsAdminTextInputWidget(),
            "label_ru": CmsAdminTextInputWidget(),
            "is_active": UnfoldBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        used = PickerFilter.objects.exclude(attribute_id=None)
        if self.instance.pk:
            used = used.exclude(pk=self.instance.pk)
        used_ids = list(used.values_list("attribute_id", flat=True))
        attr_qs = Attribute.objects.order_by("sort_order", "name")
        if self.instance.attribute_id:
            attr_qs = Attribute.objects.filter(
                Q(pk=self.instance.attribute_id) | ~Q(pk__in=used_ids)
            ).order_by("sort_order", "name")
        else:
            attr_qs = attr_qs.exclude(pk__in=used_ids)
        self.fields["attribute"].queryset = attr_qs
        self.fields["attribute"].label = "Фільтр каталогу"
        self.fields["attribute"].empty_label = "Оберіть фільтр каталогу"
        self.fields["attribute"].help_text = (
            "Варіанти підтягнуться зі значень цього фільтра."
        )
        is_new = not self.instance.pk
        self.fields["attribute"].required = is_new
        if not is_new:
            self.fields["attribute"].disabled = True
            self.fields["attribute"].required = False
        self.fields["label"].label = "Назва на головній"
        self.fields["label"].required = not is_new
        self.fields["label"].help_text = (
            "Порожнє = назва з каталогу." if is_new else ""
        )
        self.fields["label_ru"].label = "Назва на головній (RU)"
        self.fields["label_ru"].required = False
        self.fields["is_active"].label = "Показувати на головній"
        self.fields["is_active"].required = False


class PickerOptionForm(forms.ModelForm):
    class Meta:
        model = PickerFilterOption
        fields = ("label", "label_ru", "value", "price_min", "price_max")
        widgets = {
            "label": CmsAdminTextInputWidget(),
            "label_ru": CmsAdminTextInputWidget(),
            "value": forms.HiddenInput(),
            "price_min": CmsAdminTextInputWidget(),
            "price_max": CmsAdminTextInputWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["label"].label = "Варіант"
        self.fields["label"].required = False
        self.fields["label_ru"].label = "Варіант (RU)"
        self.fields["label_ru"].required = False
        self.fields["value"].required = False
        self.fields["price_min"].label = "Від ₴"
        self.fields["price_min"].required = False
        self.fields["price_max"].label = "До ₴"
        self.fields["price_max"].required = False

    def clean(self):
        cleaned = super().clean()
        label = (cleaned.get("label") or "").strip()
        if self.cleaned_data.get("DELETE"):
            return cleaned
        if not label:
            return cleaned
        value = (cleaned.get("value") or "").strip() or label
        cleaned["label"] = label
        cleaned["value"] = value
        return cleaned


def make_option_formset(filter_obj: PickerFilter, data=None):
    factory = modelformset_factory(
        PickerFilterOption,
        form=PickerOptionForm,
        extra=1,
        can_delete=True,
    )
    qs = PickerFilterOption.objects.filter(filter=filter_obj).order_by(
        "sort_order", "pk"
    )
    return factory(data=data, queryset=qs, prefix="options")


def save_option_formset(formset, filter_obj: PickerFilter) -> None:
    instances = formset.save(commit=False)
    for obj in formset.deleted_objects:
        obj.delete()
    used = set(
        PickerFilterOption.objects.filter(filter=filter_obj)
        .exclude(pk__in=[item.pk for item in instances if item.pk])
        .values_list("value", flat=True)
    )
    from catalog.filter_sort import next_sort_order

    next_order = next_sort_order(
        PickerFilterOption.objects.filter(filter=filter_obj)
    )
    for obj in instances:
        label = (obj.label or "").strip()
        if not label:
            continue
        obj.filter = filter_obj
        obj.label = label
        raw = (obj.value or label).strip()
        value = raw
        i = 1
        while value in used and (not obj.pk or obj.value != value):
            value = f"{raw}-{i}"
            i += 1
        obj.value = value
        used.add(value)
        if not obj.pk:
            obj.sort_order = next_order
            next_order += 1
        obj.is_active = True
        obj.save()
    formset.save_m2m()


def prepare_new_door(form: PickerDoorForm) -> PickerDoor:
    obj = form.save(commit=False)
    name = obj.display_name("ua") or obj.label_line1
    obj.code = ensure_unique_slug(
        PickerDoor, name, field="code", fallback="door"
    )
    from catalog.filter_sort import next_sort_order

    obj.sort_order = next_sort_order(PickerDoor.objects.all())
    return obj


def save_door_form(form: PickerDoorForm, obj: PickerDoor) -> PickerDoor:
    form.instance = obj
    obj.save()
    form.save_m2m()
    return obj


_RESERVED_FILTER_KEYS = frozenset(
    {"door", "tab", "new", "filter", "id", "q", "page", "lang"}
)


def prepare_new_filter(form: PickerFilterMetaForm) -> PickerFilter:
    from catalog.filter_sort import next_sort_order

    obj = form.save(commit=False)
    attr = obj.attribute
    seed = (attr.slug if attr is not None else "") or obj.label
    obj.key = ensure_unique_slug(
        PickerFilter, seed, field="key", fallback="filtr"
    )
    if obj.key in _RESERVED_FILTER_KEYS:
        obj.key = ensure_unique_slug(
            PickerFilter, f"{obj.key}-f", field="key", fallback="filtr"
        )
    if not (obj.label or "").strip() and attr is not None:
        obj.label = attr.name
    obj.sort_order = next_sort_order(PickerFilter.objects.all())
    return obj
