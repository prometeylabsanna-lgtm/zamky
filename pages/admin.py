from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from pages.admin_mixins import TopDropdownFiltersMixin
from pages.admin_site_content_proxies import (
    SingletonModelAdminMixin,
    register_site_content_section_admins,
)
from pages.models import ContactRequest
from pages.models_cms import SiteSettings
from pages.models_extra import (
    BlogPost,
    CallbackRequest,
    InstallRequest,
    PhotoPickImage,
    PhotoPickRequest,
)
from pages.models_media import MediaItem


@admin.register(MediaItem)
class MediaItemAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("preview", "title", "media_type", "alt_text", "file_size", "created_at")
    list_filter = ("media_type", "created_at")
    search_fields = ("title", "alt_text", "alt_text_ru", "file")
    readonly_fields = ("preview", "width", "height", "file_size", "content_hash", "created_at")
    fields = (
        "preview",
        "file",
        "media_type",
        "title",
        "alt_text",
        "alt_text_ru",
        "width",
        "height",
        "file_size",
        "content_hash",
        "created_at",
    )

    @admin.display(description="Превʼю")
    def preview(self, obj):
        if obj.pk and obj.media_type == MediaItem.MediaType.IMAGE and obj.file:
            try:
                return format_html(
                    '<img src="{}" alt="" style="max-width:96px;max-height:96px;'
                    'object-fit:cover;border-radius:8px">',
                    obj.file.url,
                )
            except Exception:
                return "—"
        return "—"

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdminMixin, ModelAdmin):
    fieldsets = (
        (
            "Основне",
            {"fields": ("site_name", "logo", "favicon")},
        ),
        (
            "Контакти",
            {
                "fields": (
                    "phone",
                    "phone_raw",
                    "email",
                    "address",
                    "address_ru",
                    "work_hours",
                    "work_hours_ru",
                )
            },
        ),
        (
            "Соцмережі",
            {"fields": ("instagram_url", "telegram_url", "facebook_url")},
        ),
        (
            "SEO за замовчуванням",
            {
                "fields": (
                    "meta_title",
                    "meta_title_ru",
                    "meta_description",
                    "meta_description_ru",
                )
            },
        ),
    )

    class Media:
        css = {"all": ("css/admin/lang_tabs.css",)}
        js = ("js/admin/lang_tabs.js",)


@admin.register(ContactRequest)
class ContactRequestAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = (
        "name",
        "phone",
        "email",
        "topic",
        "consent",
        "processed",
        "created_at",
    )
    list_filter = ("topic", "processed", "created_at", "consent")
    search_fields = ("name", "phone", "email", "message", "idempotency_key")
    readonly_fields = ("idempotency_key", "created_at")


@admin.register(CallbackRequest)
class CallbackRequestAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("name", "phone", "processed", "created_at")
    list_filter = ("processed", "created_at")
    search_fields = ("name", "phone", "idempotency_key")
    readonly_fields = ("idempotency_key", "created_at")


class PhotoPickImageInline(TabularInline):
    model = PhotoPickImage
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(PhotoPickRequest)
class PhotoPickRequestAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("phone", "channel", "processed", "created_at")
    list_filter = ("channel", "processed", "created_at")
    search_fields = ("phone", "note", "idempotency_key")
    readonly_fields = ("idempotency_key", "created_at")
    inlines = [PhotoPickImageInline]


@admin.register(InstallRequest)
class InstallRequestAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("name", "phone", "address", "processed", "created_at")
    list_filter = ("processed", "created_at")
    search_fields = ("name", "phone", "address", "comment", "idempotency_key")
    readonly_fields = ("idempotency_key", "created_at")


@admin.register(BlogPost)
class BlogPostAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("title", "slug", "is_published", "sort_order", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "slug", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")


register_site_content_section_admins()
