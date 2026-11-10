"""CMS widgets — класи Unfold (light/dark)."""

from __future__ import annotations

from typing import Any, Optional

from django.contrib.admin.widgets import AdminTextareaWidget, AdminTextInputWidget
from unfold.widgets import INPUT_CLASSES, TEXTAREA_CLASSES


class CmsAdminTextInputWidget(AdminTextInputWidget):
    def __init__(self, attrs=None):
        attrs = dict(attrs or {})
        existing = attrs.get("class", "")
        merged = list(INPUT_CLASSES)
        if existing:
            merged = list(dict.fromkeys([*merged, *existing.split()]))
        attrs["class"] = " ".join(merged)
        super().__init__(attrs=attrs)


class CmsAdminTextareaWidget(AdminTextareaWidget):
    def __init__(self, attrs=None):
        attrs = dict(attrs or {})
        rows = attrs.pop("rows", 4)
        existing = attrs.get("class", "")
        merged = list(TEXTAREA_CLASSES)
        if existing:
            merged = list(dict.fromkeys([*merged, *existing.split()]))
        attrs["class"] = " ".join(merged)
        attrs["rows"] = rows
        super().__init__(attrs=attrs)


class CmsTinyMCEWidget(AdminTextareaWidget):
    def __init__(self, attrs=None):
        attrs = dict(attrs or {})
        rows = attrs.pop("rows", 14)
        existing = attrs.get("class", "")
        merged = list(TEXTAREA_CLASSES) + ["cms-tinymce"]
        if existing:
            merged = list(dict.fromkeys([*merged, *existing.split()]))
        attrs["class"] = " ".join(merged)
        attrs["rows"] = rows
        super().__init__(attrs=attrs)

    class Media:
        js = (
            "https://cdn.jsdelivr.net/npm/tinymce@7.6.1/tinymce.min.js",
            "js/admin/cms_tinymce.js",
        )
        css = {"all": ("css/admin/cms_tinymce.css",)}


class CmsAdminColorWidget(AdminTextInputWidget):
    """Пікер кольору + HEX + кнопка «Дефолт»."""

    input_type = "color"
    template_name = "django/forms/widgets/cms_color.html"

    class Media:
        css = {"all": ("css/admin/cms_color_picker.css",)}
        js = ("js/admin/cms_color_picker.js",)

    def __init__(
        self,
        attrs: Optional[dict[str, Any]] = None,
        *,
        default_color: str = "#ffffff",
    ) -> None:
        self.default_color = self._normalize_hex(default_color) or "#ffffff"
        merged = dict(attrs or {})
        extra = merged.pop("class", "")
        classes = list(INPUT_CLASSES) + ["zamky-cms-colorpick__native"]
        if extra:
            classes = list(dict.fromkeys([*classes, *str(extra).split()]))
        super().__init__(attrs={**merged, "class": " ".join(classes)})

    @staticmethod
    def _normalize_hex(value: str) -> str:
        raw = (value or "").strip()
        if not raw:
            return ""
        if not raw.startswith("#"):
            raw = f"#{raw}"
        if len(raw) == 4 and raw.startswith("#"):
            return f"#{raw[1] * 2}{raw[2] * 2}{raw[3] * 2}".lower()
        return raw.lower()

    def format_value(self, value):
        raw = self._normalize_hex(str(value or ""))
        return raw or self.default_color

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["default_color"] = self.default_color
        context["widget"]["value"] = self.format_value(value)
        return context

