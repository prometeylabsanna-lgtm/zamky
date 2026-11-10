"""Динамічна CMS-форма секції + view."""

from __future__ import annotations

from django import forms
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanWidget

from pages.admin_guidelines import help_for_key, help_for_section
from pages.admin_hero_slides import build_hero_slide_formset
from pages.admin_site_content_widgets import (
    CmsAdminColorWidget,
    CmsAdminTextInputWidget,
    CmsAdminTextareaWidget,
    CmsTinyMCEWidget,
)
from pages.block_defaults import (
    INLINE_KEYS,
    MULTILINE_KEYS,
    STATIC_FALLBACKS,
    get_block_content_type,
    get_block_default,
    get_block_label,
    is_richtext_key,
    is_visibility_key,
)
from pages.models_cms import SITE_BLOCKS_CACHE_KEY, SiteBlock, SiteSettings
from pages.models_page_style import PageStyle
from pages.page_styles import clean_color
from pages.site_content_registry import get_section


def _image_preview_url(page: str, key: str, block: SiteBlock | None) -> tuple[str, bool]:
    if block is not None:
        if block.media_id and block.media and block.media.file:
            try:
                return block.media.file.url, False
            except Exception:
                pass
        if block.image:
            try:
                return block.image.url, False
            except Exception:
                pass
    static_path = STATIC_FALLBACKS.get((page, key), "")
    if not static_path:
        return "", False
    from django.templatetags.static import static

    return static(static_path), True


def load_section_blocks(page: str, keys: list[str]) -> dict[str, SiteBlock]:
    result: dict[str, SiteBlock] = {}
    for key in keys:
        defaults = {
            "label": get_block_label(page, key),
            "content_type": get_block_content_type(page, key),
            "text_html": get_block_default(page, key),
        }
        try:
            from pages.block_defaults_ru import get_block_default_ru

            defaults["text_html_ru"] = get_block_default_ru(page, key)
        except Exception:
            pass
        block, _ = SiteBlock.objects.get_or_create(page=page, key=key, defaults=defaults)
        result[key] = block
    return result


class SitePageContentForm(forms.Form):
    def __init__(self, *args, section=None, blocks=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.section = section
        self.blocks = blocks or {}
        self._page_style = None
        if not section:
            return

        style = PageStyle.for_page(section.page_slug)
        self._page_style = style
        self.fields["style_background"] = forms.CharField(
            required=False,
            label="Колір фону",
            initial=(style.background_color or "").strip() or PageStyle.DEFAULT_BACKGROUND,
            widget=CmsAdminColorWidget(default_color=PageStyle.DEFAULT_BACKGROUND),
            help_text=f"За замовчуванням: {PageStyle.DEFAULT_BACKGROUND}",
        )
        self.fields["style_text"] = forms.CharField(
            required=False,
            label="Колір шрифту",
            initial=(style.text_color or "").strip() or PageStyle.DEFAULT_TEXT,
            widget=CmsAdminColorWidget(default_color=PageStyle.DEFAULT_TEXT),
            help_text=f"За замовчуванням: {PageStyle.DEFAULT_TEXT}",
        )
        self.fields["style_accent"] = forms.CharField(
            required=False,
            label="Колір підсвітки",
            initial=(style.accent_color or "").strip() or PageStyle.DEFAULT_ACCENT,
            widget=CmsAdminColorWidget(default_color=PageStyle.DEFAULT_ACCENT),
            help_text=f"За замовчуванням: {PageStyle.DEFAULT_ACCENT}",
        )

        if section.visibility_key:
            block = self.blocks.get(section.visibility_key)
            initial = True
            if block is not None:
                initial = block.text_html not in {"0", "false", "False", ""}
            self.fields["section_visible"] = forms.BooleanField(
                required=False,
                initial=initial,
                label="Показувати секцію на сайті",
                widget=UnfoldBooleanWidget(),
            )

        for page, key in section.blocks:
            if section.visibility_key and key == section.visibility_key:
                continue
            block = self.blocks[key]
            ctype = get_block_content_type(page, key)
            label = block.label or get_block_label(page, key)
            help_text = help_for_key(key, page=page)

            if is_visibility_key(key):
                self.fields[f"block__{page}__{key}__visible"] = forms.BooleanField(
                    required=False,
                    initial=block.text_html not in {"0", "false", "False", ""},
                    label=label,
                    help_text=help_text,
                    widget=UnfoldBooleanWidget(),
                )
                continue

            if ctype == "image":
                self.fields[f"block__{page}__{key}__image"] = forms.ImageField(
                    required=False,
                    label=label,
                    help_text=help_text,
                    widget=UnfoldAdminFileFieldWidget(),
                )
                continue

            if ctype == "url":
                self.fields[f"block__{page}__{key}__link_url"] = forms.CharField(
                    required=False,
                    initial=block.link_url or block.text_html or get_block_default(page, key),
                    label=label,
                    help_text=help_text,
                    widget=CmsAdminTextInputWidget(),
                )
                continue

            pair = (page, key)
            if is_richtext_key(page, key):
                widget = CmsTinyMCEWidget(attrs={"rows": 14})
                ru_widget = CmsTinyMCEWidget(attrs={"rows": 14})
            elif pair in INLINE_KEYS:
                widget = CmsAdminTextInputWidget()
                ru_widget = CmsAdminTextInputWidget()
            elif pair in MULTILINE_KEYS:
                widget = CmsAdminTextareaWidget(attrs={"rows": 6})
                ru_widget = CmsAdminTextareaWidget(attrs={"rows": 6})
            else:
                widget = CmsAdminTextareaWidget(attrs={"rows": 2})
                ru_widget = CmsAdminTextareaWidget(attrs={"rows": 2})

            self.fields[f"block__{page}__{key}__text_html"] = forms.CharField(
                required=False,
                initial=block.text_html,
                label=label,
                help_text=help_text,
                widget=widget,
            )
            self.fields[f"block__{page}__{key}__text_html_ru"] = forms.CharField(
                required=False,
                initial=getattr(block, "text_html_ru", "") or "",
                label=f"{label} (RU)",
                help_text="Порожнє = український текст на вітрині.",
                widget=ru_widget,
            )

    def clean_style_background(self):
        return clean_color(
            self.cleaned_data.get("style_background", ""),
            default=PageStyle.DEFAULT_BACKGROUND,
        )

    def clean_style_text(self):
        return clean_color(
            self.cleaned_data.get("style_text", ""),
            default=PageStyle.DEFAULT_TEXT,
        )

    def clean_style_accent(self):
        return clean_color(
            self.cleaned_data.get("style_accent", ""),
            default=PageStyle.DEFAULT_ACCENT,
        )

    def save(self):
        section = self.section
        if section.visibility_key:
            visible = self.cleaned_data.get("section_visible", True)
            block = self.blocks[section.visibility_key]
            block.text_html = "1" if visible else "0"
            block.content_type = SiteBlock.ContentType.TEXT
            block.save(update_fields=["text_html", "content_type"])

        for name, value in self.cleaned_data.items():
            if not name.startswith("block__"):
                continue
            parts = name.split("__")
            if len(parts) != 4:
                continue
            _, page, key, suffix = parts
            block = self.blocks[key]
            if suffix == "visible":
                block.text_html = "1" if value else "0"
                block.save(update_fields=["text_html"])
            elif suffix == "text_html":
                block.text_html = value or ""
                block.save(update_fields=["text_html"])
            elif suffix == "text_html_ru":
                block.text_html_ru = value or ""
                block.save(update_fields=["text_html_ru"])
            elif suffix == "image":
                if value:
                    block.image = value
                    block.content_type = SiteBlock.ContentType.IMAGE
                    block.save(update_fields=["image", "content_type"])
            elif suffix == "link_url":
                block.link_url = value or ""
                block.content_type = SiteBlock.ContentType.URL
                block.text_html = value or ""
                block.save(update_fields=["link_url", "content_type", "text_html"])

        if self._page_style is not None:
            style = self._page_style
            style.background_color = self.cleaned_data.get("style_background", "")
            style.text_color = self.cleaned_data.get("style_text", "")
            style.accent_color = self.cleaned_data.get("style_accent", "")
            style.save()

        cache.delete(SITE_BLOCKS_CACHE_KEY)


def site_content_section_view(request, page_slug: str, section_slug: str, model_admin=None):
    section = get_section(page_slug, section_slug)
    if section is None:
        messages.error(request, "Секцію не знайдено.")
        return redirect("admin:index")

    keys = [key for _, key in section.blocks]
    blocks = load_section_blocks(section.page_slug, keys)
    hero_formset = None

    if request.method == "POST":
        form = SitePageContentForm(
            request.POST, request.FILES, section=section, blocks=blocks
        )
        if section.has_hero_slides:
            hero_formset = build_hero_slide_formset(
                data=request.POST, files=request.FILES
            )
        ok = form.is_valid() and (hero_formset is None or hero_formset.is_valid())
        if ok:
            form.save()
            if hero_formset is not None:
                hero_formset.save()
            messages.success(request, "Збережено.")
            return redirect(request.path)
    else:
        form = SitePageContentForm(section=section, blocks=blocks)
        if section.has_hero_slides:
            hero_formset = build_hero_slide_formset()

    field_groups = []
    style_fields = []
    for fname in ("style_background", "style_text", "style_accent"):
        if fname in form.fields:
            style_fields.append(
                {
                    "field": form[fname],
                    "field_ru": None,
                    "preview_url": "",
                    "preview_fallback": False,
                }
            )

    for group in section.field_groups:
        bound = []
        for key in group.keys:
            if section.visibility_key and key == section.visibility_key:
                if "section_visible" in form.fields:
                    bound.append(
                        {
                            "field": form["section_visible"],
                            "field_ru": None,
                            "preview_url": "",
                            "preview_fallback": False,
                        }
                    )
                continue
            page = section.page_slug
            ctype = get_block_content_type(page, key)
            if is_visibility_key(key):
                name = f"block__{page}__{key}__visible"
            elif ctype == "image":
                name = f"block__{page}__{key}__image"
            elif ctype == "url":
                name = f"block__{page}__{key}__link_url"
            else:
                name = f"block__{page}__{key}__text_html"
            if name not in form.fields:
                continue
            preview_url = ""
            preview_fallback = False
            if ctype == "image":
                preview_url, preview_fallback = _image_preview_url(
                    page, key, blocks.get(key)
                )
            item = {
                "field": form[name],
                "field_ru": None,
                "preview_url": preview_url,
                "preview_fallback": preview_fallback,
                "preview_contain": False,
            }
            ru_name = f"block__{page}__{key}__text_html_ru"
            if (
                ctype not in {"image", "url"}
                and not is_visibility_key(key)
                and ru_name in form.fields
            ):
                item["field_ru"] = form[ru_name]
            bound.append(item)
        field_groups.append(
            {
                "title": group.title,
                "description": group.description,
                "fields": bound,
                "keys": group.keys,
            }
        )

    context = {
        **(model_admin.admin_site.each_context(request) if model_admin else {}),
        "title": section.title,
        "section": section,
        "section_hint": help_for_section(section.page_slug, section.slug),
        "form": form,
        "field_groups": field_groups,
        "style_fields": style_fields,
        "style_defaults": {
            "background": PageStyle.DEFAULT_BACKGROUND,
            "text": PageStyle.DEFAULT_TEXT,
            "accent": PageStyle.DEFAULT_ACCENT,
        },
        "blocks_map": blocks,
        "hero_formset": hero_formset,
        "opts": SiteSettings._meta,
        "has_view_permission": True,
        "has_change_permission": True,
        "preview_url": section.preview_url,
        "media": form.media,
    }
    if hero_formset is not None:
        context["media"] += hero_formset.media
    return render(request, "admin/pages/site_content_page.html", context)
