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
    fieldsets = (
        (
            'Основне',
            {
                'fields': (
                    'name',
                    'slug',
                    'short',
                    'name_locative',
                    'delivery_note',
                    'areas',
                    'is_active',
                    'sort_order',
                ),
            },
        ),
        (
            'Сторінка району',
            {
                'fields': ('h1', 'seo_text', 'others_title', 'others_title_ru'),
                'description': (
                    'Блок унизу сторінки району: SEO-текст і заголовок списку '
                    'інших районів.'
                ),
            },
        ),
    )

    class Media:
        js = ('js/admin/char_hint.js',)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        locative = form.base_fields.get('name_locative')
        if locative is not None:
            locative.help_text = (
                'Наприклад «Оболонському» — у фразах «доставка в … районі».'
            )
        h1 = form.base_fields.get('h1')
        if h1 is not None:
            h1.help_text = 'Великий заголовок сторінки району. Порожнє — назва району.'
        from pages.admin_guidelines import apply_form_char_hints

        apply_form_char_hints(form)
        return form

    def get_changeform_initial_data(self, request):
        from catalog.filter_sort import next_sort_order

        initial = super().get_changeform_initial_data(request)
        initial['sort_order'] = next_sort_order(DeliveryDistrict.objects.all())
        return initial


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
                    'district',
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
