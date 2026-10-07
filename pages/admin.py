from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ContactRequest


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
