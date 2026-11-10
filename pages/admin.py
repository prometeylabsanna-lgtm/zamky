from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from pages.admin_image_preview import admin_image_preview
from pages.admin_mixins import TopDropdownFiltersMixin
from pages.admin_recent_actions import patch_admin_urls
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

patch_admin_urls()


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
        if obj.pk and obj.media_type == MediaItem.MediaType.IMAGE:
            return admin_image_preview(obj.file, max_size=96)
        return "—"

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdminMixin, ModelAdmin):
    readonly_fields = ("logo_preview", "favicon_preview")
    fieldsets = (
        (
            "Основне",
            {"fields": ("site_name", "logo_preview", "logo", "favicon_preview", "favicon")},
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

    @admin.display(description="Превʼю логотипу")
    def logo_preview(self, obj):
        return admin_image_preview(getattr(obj, "logo", None), max_size=120)

    @admin.display(description="Превʼю favicon")
    def favicon_preview(self, obj):
        return admin_image_preview(getattr(obj, "favicon", None), max_size=64)


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
    fields = ("preview", "image", "created_at")
    readonly_fields = ("preview", "created_at")
    verbose_name = "Фото"
    verbose_name_plural = "Зображення"

    @admin.display(description="Превʼю")
    def preview(self, obj):
        return admin_image_preview(getattr(obj, "image", None), max_size=96)


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
    list_display = ("cover_thumb", "title", "slug", "is_published", "sort_order", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "slug", "excerpt", "body")
    readonly_fields = ("slug", "cover_preview", "created_at", "updated_at")
    fields = (
        "title",
        "slug",
        "cover_preview",
        "cover",
        "excerpt",
        "body",
        "is_published",
        "sort_order",
        "created_at",
        "updated_at",
    )

    @admin.display(description="")
    def cover_thumb(self, obj):
        return admin_image_preview(getattr(obj, "cover", None), max_size=48)

    @admin.display(description="Превʼю обкладинки")
    def cover_preview(self, obj):
        return admin_image_preview(getattr(obj, "cover", None), max_size=180)


register_site_content_section_admins()
