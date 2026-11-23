"""Превʼю зображень у Django/Unfold адмінці."""

from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe


def _file_url(file_field) -> str:
    if not file_field:
        return ""
    try:
        return file_field.url or ""
    except Exception:
        return ""


def admin_image_preview(
    file_field,
    *,
    max_size: int = 96,
    fallback_static: str = "",
) -> str:
    url = _file_url(file_field)
    if not url and fallback_static:
        try:
            url = static(fallback_static)
        except Exception:
            url = ""
    if not url:
        return format_html(
            '<span class="admin-img-preview" data-admin-img-preview '
            'data-admin-img-max="{}">—</span>',
            max_size,
        )
    return format_html(
        '<span class="admin-img-preview" data-admin-img-preview '
        'data-admin-img-max="{0}">'
        '<img src="{1}" alt="" loading="lazy" decoding="async" '
        'style="max-width:{0}px;max-height:{0}px">'
        "</span>",
        max_size,
        url,
    )


def admin_image_preview_display(description: str = "Превʼю", max_size: int = 96):
    """Декоратор-фабрика для @admin.display з превʼю поля ImageField."""

    def decorator(field_name: str):
        def method(self, obj):
            if not obj or not getattr(obj, "pk", None):
                return "—"
            return admin_image_preview(getattr(obj, field_name, None), max_size=max_size)

        method.short_description = description
        return method

    return decorator


EMPTY_PREVIEW = mark_safe("—")
