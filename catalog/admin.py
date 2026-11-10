from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from pages.admin_image_preview import admin_image_preview
from pages.admin_mixins import DefaultActiveTrueFilterMixin, TopDropdownFiltersMixin

from .admin_product_actions import PRODUCT_ACTIONS
from .models import (
    Attribute,
    AttributeGroup,
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductImage,
)


class AttributeValueInline(TabularInline):
    model = AttributeValue
    extra = 1
    tab = True
    verbose_name = 'Значення фільтра'
    verbose_name_plural = 'Значення фільтрів'
    readonly_fields = ('slug',)
    fields = ('value', 'slug', 'sort_order')


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    tab = True
    fields = ('preview', 'image', 'alt', 'sort_order', 'is_primary')
    readonly_fields = ('preview',)
    verbose_name = 'Зображення товару'
    verbose_name_plural = 'Зображення товарів'

    @admin.display(description='Превʼю')
    def preview(self, obj):
        return admin_image_preview(getattr(obj, 'image', None), max_size=72)


class ProductAttributeInline(TabularInline):
    model = ProductAttribute
    extra = 1
    autocomplete_fields = ('attribute_value',)
    tab = True
    verbose_name = 'Значення фільтра'
    verbose_name_plural = 'Фільтри товару'


@admin.register(Category)
class CategoryAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('logo_thumb', 'name', 'slug', 'parent', 'sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug')
    readonly_fields = ('slug', 'logo_preview')
    fields = (
        'name',
        'slug',
        'parent',
        'logo_preview',
        'logo',
        'icon',
        'sort_order',
        'is_active',
    )

    @admin.display(description='')
    def logo_thumb(self, obj):
        return admin_image_preview(getattr(obj, 'logo', None), max_size=40)

    @admin.display(description='Превʼю логотипу')
    def logo_preview(self, obj):
        return admin_image_preview(getattr(obj, 'logo', None), max_size=96)


@admin.register(AttributeGroup)
class AttributeGroupAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    search_fields = ('name', 'slug')
    readonly_fields = ('slug',)


@admin.register(Attribute)
class AttributeAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'slug', 'group', 'filterable', 'sort_order')
    list_filter = ('filterable', 'group')
    search_fields = ('name', 'slug')
    autocomplete_fields = ('group',)
    readonly_fields = ('slug',)
    inlines = [AttributeValueInline]


@admin.register(AttributeValue)
class AttributeValueAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('value', 'attribute', 'slug', 'sort_order')
    list_filter = ('attribute',)
    search_fields = ('value', 'slug')
    autocomplete_fields = ('attribute',)
    readonly_fields = ('slug',)


@admin.register(Product)
class ProductAdmin(DefaultActiveTrueFilterMixin, TopDropdownFiltersMixin, ModelAdmin):
    list_display = (
        'name',
        'sku',
        'category',
        'price',
        'stock',
        'is_active',
        'is_hit',
        'is_new',
    )
    list_display_links = ('name', 'sku')
    list_filter = (
        'is_active',
        'is_hit',
        'is_new',
        'category',
        'brand',
        'color_label',
    )
    search_fields = ('name', 'name_ru', 'sku', 'brand', 'color_label')
    autocomplete_fields = ('category',)
    readonly_fields = ('slug', 'og_preview', 'created_at', 'updated_at')
    inlines = [ProductImageInline, ProductAttributeInline]
    list_editable = ('stock', 'is_active', 'is_hit', 'is_new')
    actions = PRODUCT_ACTIONS
    actions_on_top = True
    actions_on_bottom = True

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            func, name, _desc = actions['delete_selected']
            actions['delete_selected'] = (func, name, 'Видалити вибрані')
        return actions

    fieldsets = (
        (
            'Основне',
            {
                'classes': ('tab',),
                'fields': (
                    'name',
                    'name_ru',
                    'slug',
                    'sku',
                    'category',
                    'brand',
                    'price',
                    'old_price',
                    'stock',
                    'catalog_order',
                    'rating',
                    'is_active',
                    'is_hit',
                    'is_new',
                    'color_code',
                    'color_label',
                    'finish',
                    'cover',
                    'size_mm',
                    'size_a',
                    'size_b',
                    'created_at',
                    'updated_at',
                ),
            },
        ),
        (
            'Опис',
            {
                'classes': ('tab',),
                'fields': (
                    'short_description',
                    'short_description_ru',
                    'description',
                    'description_ru',
                ),
            },
        ),
        (
            'SEO',
            {
                'classes': ('tab',),
                'fields': (
                    'seo_title',
                    'seo_title_ru',
                    'seo_description',
                    'seo_description_ru',
                    'canonical_url',
                    'og_preview',
                    'og_image',
                ),
            },
        ),
    )

    class Media:
        css = {'all': ('css/admin/lang_tabs.css',)}
        js = ('js/admin/lang_tabs.js',)

    @admin.display(description='Превʼю OG')
    def og_preview(self, obj):
        return admin_image_preview(getattr(obj, 'og_image', None), max_size=160)


@admin.register(ProductImage)
class ProductImageAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('preview', 'product', 'sort_order', 'is_primary', 'alt')
    list_filter = ('is_primary',)
    search_fields = ('product__name', 'product__sku', 'alt')
    readonly_fields = ('preview',)
    fields = ('preview', 'product', 'image', 'alt', 'sort_order', 'is_primary')

    @admin.display(description='Превʼю')
    def preview(self, obj):
        return admin_image_preview(getattr(obj, 'image', None), max_size=80)
