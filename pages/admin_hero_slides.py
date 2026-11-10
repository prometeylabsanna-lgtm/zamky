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
            "media",
            "image",
            "alt_text",
            "alt_text_ru",
            "link_url",
            "sort_order",
            "is_active",
        )
        widgets = {
            "image": UnfoldAdminFileFieldWidget(),
            "alt_text": CmsAdminTextInputWidget(),
            "alt_text_ru": CmsAdminTextInputWidget(),
            "link_url": CmsAdminTextInputWidget(),
            "sort_order": forms.HiddenInput(),
            "is_active": UnfoldBooleanWidget(),
        }

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
        extra=1,
        can_delete=True,
    )
    queryset = HeroSlide.objects.all().order_by("sort_order", "id")
    return FormSet(data=data, files=files, queryset=queryset, prefix="hero_slides")
