from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from pages.admin_mixins import TopDropdownFiltersMixin

from .models import DeliveryDistrict, Order, OrderItem, QuickOrder


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'sku', 'unit_price', 'quantity', 'line_total')
    can_delete = False
    tab = True
    verbose_name = 'Позиція'
    verbose_name_plural = 'Позиції'


@admin.register(DeliveryDistrict)
class DeliveryDistrictAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'slug', 'short', 'delivery_note', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'short')
    readonly_fields = ('slug',)


@admin.register(QuickOrder)
class QuickOrderAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('phone', 'name', 'product', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('phone', 'name', 'product__sku', 'product__name')
    autocomplete_fields = ('product',)


@admin.register(Order)
class OrderAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = (
        'number',
        'status',
        'first_name',
        'phone',
        'total',
        'delivery_method',
        'payment_method',
        'created_at',
    )
    list_filter = ('status', 'delivery_method', 'payment_method', 'created_at')
    search_fields = ('number', 'first_name', 'last_name', 'phone', 'email', 'idempotency_key')
    readonly_fields = (
        'number',
        'idempotency_key',
        'subtotal',
        'delivery_price',
        'total',
        'created_at',
        'updated_at',
    )
    inlines = [OrderItemInline]
