"""HeroSlide ModelFormSet для CMS-секції hero."""

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanWidget

from pages.admin_site_content_widgets import CmsAdminTextInputWidget
from pages.hero_slides import ensure_default_hero_slides
from pages.models_cms import HeroSlide


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = (
            "image",
            "alt_text",
            "alt_text_ru",
            "link_url",
            "headline",
            "headline_ru",
            "headline_accent",
            "headline_accent_ru",
            "subtitle",
            "subtitle_ru",
            "cta_primary_label",
            "cta_primary_label_ru",
            "cta_primary_url",
            "cta_secondary_label",
            "cta_secondary_label_ru",
            "cta_secondary_url",
            "sort_order",
            "is_active",
            "show_secondary",
            "cta_primary_light",
            "show_features",
            "show_brands",
        )
        widgets = {
            "image": UnfoldAdminFileFieldWidget(attrs={"accept": "image/*"}),
            "alt_text": CmsAdminTextInputWidget(),
            "alt_text_ru": CmsAdminTextInputWidget(),
            "link_url": CmsAdminTextInputWidget(),
            "headline": CmsAdminTextInputWidget(),
            "headline_ru": CmsAdminTextInputWidget(),
            "headline_accent": CmsAdminTextInputWidget(),
            "headline_accent_ru": CmsAdminTextInputWidget(),
            "subtitle": CmsAdminTextInputWidget(),
            "subtitle_ru": CmsAdminTextInputWidget(),
            "cta_primary_label": CmsAdminTextInputWidget(),
            "cta_primary_label_ru": CmsAdminTextInputWidget(),
            "cta_primary_url": CmsAdminTextInputWidget(),
            "cta_secondary_label": CmsAdminTextInputWidget(),
            "cta_secondary_label_ru": CmsAdminTextInputWidget(),
            "cta_secondary_url": CmsAdminTextInputWidget(),
            "sort_order": forms.HiddenInput(),
            "is_active": UnfoldBooleanWidget(),
            "show_secondary": UnfoldBooleanWidget(),
            "cta_primary_light": UnfoldBooleanWidget(),
            "show_features": UnfoldBooleanWidget(),
            "show_brands": UnfoldBooleanWidget(),
        }

    def overlay_fields(self):
        names = (
            ("headline", "headline_ru"),
            ("headline_accent", "headline_accent_ru"),
            ("subtitle", "subtitle_ru"),
        )
        return [[self[name] for name in pair] for pair in names]

    def cta_columns(self):
        names = (
            ("cta_primary_label", "cta_primary_label_ru", "cta_primary_url"),
            ("cta_secondary_label", "cta_secondary_label_ru", "cta_secondary_url"),
        )
        return [[self[name] for name in col] for col in names]

    def clean(self):
        cleaned = super().clean()
        if self.cleaned_data.get("DELETE"):
            return cleaned
        image = cleaned.get("image")
        has_existing = bool(getattr(self.instance, "pk", None) and self.instance.image)
        has_static = bool(getattr(self.instance, "static_fallback", ""))
        if not image and not has_existing and not has_static and not cleaned.get("alt_text"):
            return cleaned
        return cleaned


class HeroSlideBaseFormSet(BaseModelFormSet):
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
        order = 0
        saved = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            image = form.cleaned_data.get("image")
            has_existing = bool(form.instance.pk and form.instance.image)
            has_static = bool(form.instance.static_fallback)
            alt = (form.cleaned_data.get("alt_text") or "").strip()
            if not image and not has_existing and not has_static and not alt:
                continue
            obj = form.save(commit=False)
            obj.sort_order = order
            order += 1
            if commit:
                obj.save()
            saved.append(obj)
        if commit:
            self.save_m2m()
        return saved


def build_hero_slide_formset(data=None, files=None):
    ensure_default_hero_slides()
    FormSet = modelformset_factory(
        HeroSlide,
        form=HeroSlideForm,
        formset=HeroSlideBaseFormSet,
        extra=0,
        can_delete=True,
    )
    queryset = HeroSlide.objects.all().order_by("sort_order", "id")
    return FormSet(data=data, files=files, queryset=queryset, prefix="hero_slides")
