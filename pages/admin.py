from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import ContactRequest
from .models_extra import (
    BlogPost,
    CallbackRequest,
    InstallRequest,
    PhotoPickImage,
    PhotoPickRequest,
)


@admin.register(ContactRequest)
class ContactRequestAdmin(ModelAdmin):
    list_display = (
        'name',
        'phone',
        'email',
        'topic',
        'consent',
        'processed',
        'created_at',
    )
    list_filter = ('topic', 'processed', 'created_at', 'consent')
    search_fields = ('name', 'phone', 'email', 'message', 'idempotency_key')
    readonly_fields = ('idempotency_key', 'created_at')


@admin.register(CallbackRequest)
class CallbackRequestAdmin(ModelAdmin):
    list_display = ('name', 'phone', 'processed', 'created_at')
    list_filter = ('processed', 'created_at')
    search_fields = ('name', 'phone', 'idempotency_key')
    readonly_fields = ('idempotency_key', 'created_at')


class PhotoPickImageInline(TabularInline):
    model = PhotoPickImage
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(PhotoPickRequest)
class PhotoPickRequestAdmin(ModelAdmin):
    list_display = ('phone', 'channel', 'processed', 'created_at')
    list_filter = ('channel', 'processed', 'created_at')
    search_fields = ('phone', 'note', 'idempotency_key')
    readonly_fields = ('idempotency_key', 'created_at')
    inlines = [PhotoPickImageInline]


@admin.register(InstallRequest)
class InstallRequestAdmin(ModelAdmin):
    list_display = ('name', 'phone', 'address', 'processed', 'created_at')
    list_filter = ('processed', 'created_at')
    search_fields = ('name', 'phone', 'address', 'comment', 'idempotency_key')
    readonly_fields = ('idempotency_key', 'created_at')


@admin.register(BlogPost)
class BlogPostAdmin(ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'sort_order', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'slug', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
