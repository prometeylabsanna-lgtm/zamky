"""CMS «Головна — Категорії»: кнопки карток + деталі (фото, назва, підпис)."""

from __future__ import annotations

from django import forms
from django.contrib import messages
from django.db.models import Max
from django.shortcuts import redirect, render
from django.urls import reverse
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanWidget

from catalog.models import Category
from pages.admin_guidelines import help_for_section
from pages.admin_site_content import SitePageContentForm, load_section_blocks
from pages.admin_site_content_widgets import CmsAdminTextInputWidget
from pages.models_cms import SiteSettings
from pages.page_styles import PageStyle
from pages.site_content_registry import get_section
from pages.slug_utils import ensure_unique_slug

_FALLBACKS = (
    "img/v2/p2_8.png",
    "img/v2/p2_9.png",
    "img/v2/p2_10.png",
    "img/v2/p2_11.png",
    "img/v2/p2_12.png",
    "img/v2/p2_13.png",
)


class HomeCategoryCardForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            "name",
            "name_ru",
            "home_subtitle",
            "home_subtitle_ru",
            "logo",
            "is_active",
        )
        widgets = {
            "name": CmsAdminTextInputWidget(),
            "name_ru": CmsAdminTextInputWidget(),
            "home_subtitle": CmsAdminTextInputWidget(),
            "home_subtitle_ru": CmsAdminTextInputWidget(),
            "logo": UnfoldAdminFileFieldWidget(
                attrs={"accept": "image/png,image/jpeg,image/webp,image/svg+xml,.svg"}
            ),
            "is_active": UnfoldBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].label = "Назва"
        self.fields["name_ru"].label = "Назва (RU)"
        self.fields["name_ru"].required = False
        self.fields["home_subtitle"].label = "Підпис"
        self.fields["home_subtitle"].required = False
        self.fields["home_subtitle_ru"].label = "Підпис (RU)"
        self.fields["home_subtitle_ru"].required = False
        self.fields["logo"].label = "Картинка"
        self.fields["logo"].required = False
        self.fields["is_active"].label = "Показувати на головній"
        self.fields["is_active"].required = False
        self.fields["home_subtitle"].help_text = "Сірий рядок під назвою на картці."
        self.fields["logo"].help_text = "Квадратне фото або лого. Порожнє = стандартне."


def _section_url(cat: Category | None = None, *, new: bool = False) -> str:
    url = reverse("admin:pages_homecategoriessettings_change", args=[1])
    if new:
        return f"{url}?new=1"
    if cat is not None and cat.pk:
        return f"{url}?cat={cat.pk}"
    return url


def _preview_url(cat: Category | None, index: int) -> tuple[str, bool]:
    if cat is not None and cat.logo:
        try:
            return cat.logo.url, False
        except Exception:
            pass
    from django.templatetags.static import static

    path = _FALLBACKS[index % len(_FALLBACKS)]
    return static(path), True


def _next_sort_order() -> int:
    current = (
        Category.objects.filter(parent__isnull=True).aggregate(m=Max("sort_order"))["m"]
        or 0
    )
    return current + 1


def home_categories_section_view(request, model_admin=None):
    section = get_section("home", "categories")
    if section is None:
        messages.error(request, "Секцію не знайдено.")
        return redirect("admin:index")

    keys = [key for _, key in section.blocks]
    blocks = load_section_blocks(section.page_slug, keys)
    cats = list(
        Category.objects.filter(parent__isnull=True).order_by("sort_order", "name", "pk")
    )

    is_new = request.GET.get("new") == "1"
    cat = None
    if not is_new:
        raw = (request.GET.get("cat") or "").strip()
        if raw.isdigit():
            cat = next((item for item in cats if item.pk == int(raw)), None)
        elif cats:
            cat = cats[0]
            is_new = False

    if request.method == "POST":
        section_form = SitePageContentForm(
            request.POST, request.FILES, section=section, blocks=blocks
        )
        instance = None if request.POST.get("card_new") == "1" else cat
        card_form = HomeCategoryCardForm(
            request.POST, request.FILES, instance=instance
        )
        ok_section = section_form.is_valid()
        ok_card = card_form.is_valid()
        if ok_section:
            section_form.save()
        if ok_card:
            obj = card_form.save(commit=False)
            if instance is None:
                obj.parent = None
                obj.sort_order = _next_sort_order()
                obj.slug = ensure_unique_slug(
                    Category, obj.name, fallback="category"
                )
            obj.save()
            messages.success(request, "Збережено.")
            return redirect(_section_url(obj))
        blank_new = instance is None and not (request.POST.get("name") or "").strip()
        if ok_section and blank_new:
            messages.success(request, "Збережено.")
            return redirect(_section_url(new=True) if is_new else _section_url())
        messages.error(request, "Перевірте поля категорії.")
    else:
        section_form = SitePageContentForm(section=section, blocks=blocks)
        if is_new:
            card_form = HomeCategoryCardForm(initial={"is_active": True})
        elif cat is not None:
            card_form = HomeCategoryCardForm(instance=cat)
        else:
            card_form = None

    vis_item = None
    if "section_visible" in section_form.fields:
        vis_item = section_form["section_visible"]

    style_fields = []
    for fname in ("style_background", "style_text", "style_accent"):
        if fname in section_form.fields:
            style_fields.append({"field": section_form[fname]})

    nav = []
    for i, item in enumerate(cats):
        preview, fallback = _preview_url(item, i)
        nav.append(
            {
                "id": item.pk,
                "name": item.name,
                "url": _section_url(item),
                "active": cat is not None and item.pk == cat.pk and not is_new,
                "inactive": not item.is_active,
                "preview": preview,
                "preview_fallback": fallback,
            }
        )

    selected_index = 0
    if cat is not None:
        selected_index = next(
            (i for i, item in enumerate(cats) if item.pk == cat.pk), 0
        )
    preview_url, preview_fallback = _preview_url(
        None if is_new else cat, selected_index
    )

    media = section_form.media
    if card_form is not None:
        media = media + card_form.media

    context = {
        **(model_admin.admin_site.each_context(request) if model_admin else {}),
        "title": section.title,
        "section": section,
        "section_hint": help_for_section(section.page_slug, section.slug),
        "form": section_form,
        "card_form": card_form,
        "is_new": is_new,
        "current_cat": cat,
        "category_nav": nav,
        "add_url": _section_url(new=True),
        "preview_url": section.preview_url,
        "card_preview_url": preview_url if card_form is not None else "",
        "card_preview_fallback": preview_fallback,
        "vis_item": vis_item,
        "style_fields": style_fields,
        "style_defaults": {
            "background": PageStyle.DEFAULT_BACKGROUND,
            "text": PageStyle.DEFAULT_TEXT,
            "accent": PageStyle.DEFAULT_ACCENT,
        },
        "opts": SiteSettings._meta,
        "has_view_permission": True,
        "has_change_permission": True,
        "media": media,
    }
    return render(request, "admin/pages/home_categories_page.html", context)
