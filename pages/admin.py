from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from pages.admin_image_preview import admin_image_preview
from pages.admin_mixins import TopDropdownFiltersMixin
from pages.admin_recent_actions import patch_admin_urls
from pages.admin_site_content_proxies import (
    SingletonModelAdminMixin,
    register_site_content_section_admins,
)
from pages.admin_site_content_widgets import CmsTinyMCEWidget
from pages.legal_body import sanitize_legal_html
from pages.models import ContactRequest
from pages.models_cms import SiteSettings
from pages.models_extra import (
    BlogPost,
    CallbackRequest,
    InstallRequest,
    PhotoPickImage,
    PhotoPickRequest,
)
patch_admin_urls()


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
        # SEO за замовчуванням перенесено в «Маркетинг → SEO-налаштування»
        # (marketing/0002 копіює значення). Поля meta_* лишаються в БД, не видалені.
    )

    class Media:
        css = {"all": ("css/admin/lang_tabs.css",)}
        js = ("js/admin/lang_tabs.js", "js/admin/image_preview.js")

    @admin.display(description="Превʼю логотипу")
    def logo_preview(self, obj):
        return admin_image_preview(
            getattr(obj, "logo", None),
            max_size=120,
            fallback_static="img/logo.png",
        )

    @admin.display(description="Превʼю favicon")
    def favicon_preview(self, obj):
        return admin_image_preview(
            getattr(obj, "favicon", None),
            max_size=64,
            fallback_static="img/favicon-32x32.png",
        )


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
    list_display_links = ("title",)
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "slug", "excerpt", "body")
    readonly_fields = ("slug", "cover_preview", "created_at", "updated_at")
    fieldsets = (
        (
            "Шапка",
            {"fields": ("title", "slug", "excerpt", "cover_preview", "cover")},
        ),
        ("Текст", {"fields": ("body",)}),
        (
            "Публікація",
            {"fields": ("is_published", "sort_order", "created_at", "updated_at")},
        ),
    )

    class Media:
        js = ("js/admin/image_preview.js",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "body":
            kwargs["widget"] = CmsTinyMCEWidget(
                attrs={"rows": 22, "class": "cms-tinymce--tall"}
            )
            kwargs["help_text"] = (
                "Один редактор: заголовки (H2), абзаци, списки — як на сайті."
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.body = sanitize_legal_html(obj.body)
        super().save_model(request, obj, form, change)

    def _cover_preview(self, obj, max_size: int):
        fallback = ""
        if obj is not None:
            fallback = getattr(obj, "cover_fallback", "") or ""
        return admin_image_preview(
            getattr(obj, "cover", None),
            max_size=max_size,
            fallback_static=fallback,
        )

    @admin.display(description="")
    def cover_thumb(self, obj):
        return self._cover_preview(obj, 48)

    @admin.display(description="Превʼю обкладинки")
    def cover_preview(self, obj):
        return self._cover_preview(obj, 180)


register_site_content_section_admins()
