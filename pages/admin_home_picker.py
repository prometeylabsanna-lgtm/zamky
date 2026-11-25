"""CMS підбору: двері, фільтри, оформлення (тексти — стандартна секція)."""

from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from pages.admin_guidelines import help_for_section
from pages.admin_home_picker_forms import (
    PickerDoorForm,
    PickerFilterMetaForm,
    make_option_formset,
    prepare_new_door,
    prepare_new_filter,
    save_door_form,
    save_option_formset,
)
from pages.admin_site_content import SitePageContentForm, load_section_blocks
from pages.models_cms import SiteSettings
from pages.models_page_style import PageStyle
from pages.models_picker import PickerDoor, PickerFilter
from pages.picker_defaults import (
    door_image_url,
    ensure_picker_defaults,
    fill_options_from_attribute,
)
from pages.site_content_registry import get_section


def _url(model_name: str, **query) -> str:
    url = reverse(f"admin:pages_{model_name}_change", args=[1])
    parts = [f"{key}={value}" for key, value in query.items() if value not in (None, "")]
    if not parts:
        return url
    return f"{url}?{'&'.join(parts)}"


def _base_context(request, model_admin, section, title, media):
    return {
        **(model_admin.admin_site.each_context(request) if model_admin else {}),
        "title": title or section.title,
        "section": section,
        "section_hint": help_for_section(section.page_slug, section.slug),
        "preview_url": section.preview_url,
        "opts": SiteSettings._meta,
        "has_view_permission": True,
        "has_change_permission": True,
        "media": media,
    }


def home_picker_doors_view(request, model_admin=None):
    section = get_section("home", "picker_doors")
    if section is None:
        messages.error(request, "Секцію не знайдено.")
        return redirect("admin:index")

    ensure_picker_defaults()
    doors = list(PickerDoor.objects.order_by("sort_order", "pk"))
    is_new = request.GET.get("new") == "1"
    door = _selected_door(request, doors, is_new)

    if request.method == "POST":
        if request.POST.get("delete_door") == "1" and door is not None:
            door.delete()
            messages.success(request, "Картку дверей видалено.")
            return redirect(_url("homepickerdoorssettings"))
        instance = None if request.POST.get("door_new") == "1" else door
        door_form = PickerDoorForm(request.POST, request.FILES, instance=instance)
        if door_form.is_valid():
            if instance is None:
                if not (request.POST.get("label_line1") or "").strip():
                    messages.success(request, "Збережено.")
                    return redirect(_url("homepickerdoorssettings", new="1"))
                obj = prepare_new_door(door_form)
                save_door_form(door_form, obj)
            else:
                obj = door_form.save()
            messages.success(request, "Збережено.")
            return redirect(_url("homepickerdoorssettings", door=obj.pk))
        messages.error(request, "Перевірте поля дверей.")
    elif is_new:
        door_form = PickerDoorForm(initial={"is_active": True})
    elif door is not None:
        door_form = PickerDoorForm(instance=door)
    else:
        door_form = None

    preview_url, preview_fallback = "", False
    if door_form is not None and not is_new and door is not None:
        preview_url, fallback_path = door_image_url(door)
        if not preview_url and fallback_path:
            from django.templatetags.static import static

            preview_url = static(fallback_path)
            preview_fallback = True

    media = door_form.media if door_form is not None else None
    context = _base_context(request, model_admin, section, section.title, media)
    context.update(
        {
            "door_form": door_form,
            "is_new_door": is_new,
            "current_door": door,
            "door_nav": _door_nav(doors, door, is_new),
            "add_door_url": _url("homepickerdoorssettings", new="1"),
            "door_preview_url": preview_url,
            "door_preview_fallback": preview_fallback,
        }
    )
    return render(request, "admin/pages/home_picker_doors.html", context)


def home_picker_filters_view(request, model_admin=None):
    section = get_section("home", "picker_filters")
    if section is None:
        messages.error(request, "Секцію не знайдено.")
        return redirect("admin:index")

    ensure_picker_defaults()
    filters = list(PickerFilter.objects.order_by("sort_order", "pk"))
    is_new = request.GET.get("new") == "1"
    filt = _selected_filter(request, filters, is_new)
    filter_form = None
    option_formset = None

    if request.method == "POST":
        if request.POST.get("delete_filter") == "1" and filt is not None:
            filt.delete()
            messages.success(request, "Фільтр видалено.")
            return redirect(_url("homepickerfilterssettings"))
        instance = None if request.POST.get("filter_new") == "1" else filt
        if instance is None:
            filter_form = PickerFilterMetaForm(request.POST)
            if filter_form.is_valid():
                obj = prepare_new_filter(filter_form)
                obj.save()
                fill_options_from_attribute(obj)
                messages.success(request, "Збережено.")
                return redirect(_url("homepickerfilterssettings", filter=obj.key))
            messages.error(request, "Перевірте поля фільтра.")
            is_new = True
            filt = None
        else:
            filter_form = PickerFilterMetaForm(request.POST, instance=instance)
            option_formset = make_option_formset(instance, data=request.POST)
            if filter_form.is_valid() and option_formset.is_valid():
                filter_form.save()
                save_option_formset(option_formset, instance)
                messages.success(request, "Збережено.")
                return redirect(
                    _url("homepickerfilterssettings", filter=instance.key)
                )
            messages.error(request, "Перевірте фільтр і варіанти.")
    elif is_new:
        filter_form = PickerFilterMetaForm(initial={"is_active": True})
    elif filt is not None:
        filter_form = PickerFilterMetaForm(instance=filt)
        option_formset = make_option_formset(filt)

    media = None
    if filter_form is not None:
        media = filter_form.media
    if option_formset is not None:
        media = (media + option_formset.media) if media else option_formset.media

    context = _base_context(request, model_admin, section, section.title, media)
    context.update(
        {
            "filter_form": filter_form,
            "option_formset": option_formset,
            "is_new_filter": is_new,
            "current_filter": filt,
            "filter_nav": _filter_nav(filters, filt, is_new),
            "add_filter_url": _url("homepickerfilterssettings", new="1"),
            "show_price_bounds": bool(filt and filt.key == "price" and not is_new),
        }
    )
    return render(request, "admin/pages/home_picker_filters.html", context)


def home_picker_style_view(request, model_admin=None):
    section = get_section("home", "picker_style")
    if section is None:
        messages.error(request, "Секцію не знайдено.")
        return redirect("admin:index")

    blocks = load_section_blocks(section.page_slug, [])
    if request.method == "POST":
        form = SitePageContentForm(
            request.POST, request.FILES, section=section, blocks=blocks
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Збережено.")
            return redirect(request.path)
    else:
        form = SitePageContentForm(section=section, blocks=blocks)

    style_fields = [
        {"field": form[name]}
        for name in ("style_background", "style_text", "style_accent")
        if name in form.fields
    ]
    context = _base_context(request, model_admin, section, section.title, form.media)
    context.update(
        {
            "form": form,
            "style_fields": style_fields,
            "style_defaults": {
                "background": PageStyle.DEFAULT_BACKGROUND,
                "text": PageStyle.DEFAULT_TEXT,
                "accent": PageStyle.DEFAULT_ACCENT,
            },
        }
    )
    return render(request, "admin/pages/home_picker_style.html", context)


def _selected_door(request, doors: list[PickerDoor], is_new: bool):
    if is_new:
        return None
    raw = (request.GET.get("door") or "").strip()
    if raw.isdigit():
        found = next((item for item in doors if item.pk == int(raw)), None)
        if found is not None:
            return found
    return doors[0] if doors else None


def _selected_filter(request, filters: list[PickerFilter], is_new: bool):
    if is_new:
        return None
    raw = (request.GET.get("filter") or "").strip()
    if raw:
        found = next((item for item in filters if item.key == raw), None)
        if found is not None:
            return found
    return filters[0] if filters else None


def _door_nav(doors, current, is_new: bool) -> list[dict]:
    rows = []
    for item in doors:
        rows.append(
            {
                "name": item.display_name("ua"),
                "url": _url("homepickerdoorssettings", door=item.pk),
                "active": current is not None and item.pk == current.pk and not is_new,
                "inactive": not item.is_active,
            }
        )
    return rows


def _filter_nav(filters, current, is_new: bool) -> list[dict]:
    rows = []
    for item in filters:
        rows.append(
            {
                "name": item.label,
                "url": _url("homepickerfilterssettings", filter=item.key),
                "active": current is not None and item.pk == current.pk and not is_new,
                "inactive": not item.is_active,
            }
        )
    return rows
