"""CMS widgets — класи Unfold (light/dark)."""

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
