"""Превʼю зображень у Django/Unfold адмінці."""

from django.utils.html import format_html
from django.utils.safestring import mark_safe


def admin_image_preview(file_field, *, max_size: int = 96) -> str:
    if not file_field:
        return '—'
    try:
        url = file_field.url
    except Exception:
        return '—'
    if not url:
        return '—'
    return format_html(
        '<img src="{}" alt="" loading="lazy" decoding="async" '
        'style="max-width:{}px;max-height:{}px;width:auto;height:auto;'
        'object-fit:cover;border-radius:8px;display:block;'
        'border:1px solid #e5e7eb">',
        url,
        max_size,
        max_size,
    )


def admin_image_preview_display(description: str = 'Превʼю', max_size: int = 96):
    """Декоратор-фабрика для @admin.display з превʼю поля ImageField."""

    def decorator(field_name: str):
        def method(self, obj):
            if not obj or not getattr(obj, 'pk', None):
                return '—'
            return admin_image_preview(getattr(obj, field_name, None), max_size=max_size)

        method.short_description = description
        return method

    return decorator


EMPTY_PREVIEW = mark_safe('—')
