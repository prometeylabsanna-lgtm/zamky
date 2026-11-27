from django.contrib import admin
from django.http import HttpResponse
from unfold.admin import ModelAdmin, TabularInline

from pages.admin_mixins import TopDropdownFiltersMixin

from .ads_csv import orders_ads_csv
from .models import Order, OrderItem, QuickOrder


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'sku', 'unit_price', 'quantity', 'line_total')
    can_delete = False
    tab = True
    verbose_name = 'Позиція'
    verbose_name_plural = 'Позиції'


def export_orders_ads_csv(modeladmin, request, queryset):
    body = orders_ads_csv(queryset)
    response = HttpResponse(body, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="orders-ads.csv"'
    return response


export_orders_ads_csv.short_description = 'Експорт CSV для реклами'


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
        'city',
        'address',
        'total',
        'delivery_method',
        'payment_method',
        'created_at',
    )
    list_filter = ('status', 'delivery_method', 'payment_method', 'created_at')
    search_fields = (
        'number',
        'first_name',
        'last_name',
        'phone',
        'email',
        'city',
        'address',
        'idempotency_key',
    )
    actions = (export_orders_ads_csv,)
    actions_on_top = True
    readonly_fields = (
        'number',
        'idempotency_key',
        'payment_ref',
        'reserved_until',
        'subtotal',
        'delivery_price',
        'total',
        'created_at',
        'updated_at',
        'np_city_ref',
        'np_warehouse_ref',
        'np_warehouse_snapshot',
    )
    fieldsets = (
        (
            'Замовлення',
            {'fields': ('number', 'status', 'created_at', 'updated_at')},
        ),
        (
            'Покупець',
            {'fields': ('first_name', 'last_name', 'phone', 'email', 'comment')},
        ),
        (
            'Доставка',
            {
                'fields': (
                    'delivery_method',
                    'city',
                    'address',
                    'np_city_ref',
                    'np_warehouse_ref',
                    'np_warehouse_snapshot',
                ),
            },
        ),
        (
            'Оплата',
            {
                'fields': (
                    'payment_method',
                    'payment_ref',
                    'reserved_until',
                    'subtotal',
                    'delivery_price',
                    'total',
                    'idempotency_key',
                ),
            },
        ),
    )
    inlines = [OrderItemInline]
