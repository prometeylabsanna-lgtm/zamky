from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from pages.admin_mixins import DefaultActiveTrueFilterMixin, TopDropdownFiltersMixin

from .models import (
    Attribute,
    AttributeGroup,
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductFamily,
    ProductImage,
)


class AttributeValueInline(TabularInline):
    model = AttributeValue
    extra = 1
    tab = True
    verbose_name = 'Значення атрибута'
    verbose_name_plural = 'Значення атрибутів'


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
        if obj.pk and obj.image:
            try:
                return format_html(
                    '<img src="{}" alt="" style="max-width:72px;max-height:72px;'
                    'object-fit:cover;border-radius:6px">',
                    obj.image.url,
                )
            except Exception:
                return '—'
        return '—'


class ProductAttributeInline(TabularInline):
    model = ProductAttribute
    extra = 1
    autocomplete_fields = ('attribute_value',)
    tab = True
    verbose_name = 'Характеристика'
    verbose_name_plural = 'Характеристики'


class ProductVariantInline(TabularInline):
    model = Product
    fk_name = 'family'
    extra = 0
    fields = (
        'sku',
        'color_code',
        'color_label',
        'size_mm',
        'price',
        'stock',
        'is_active',
    )
    show_change_link = True
    tab = True
    verbose_name = 'Варіант'
    verbose_name_plural = 'Варіанти'


@admin.register(Category)
class CategoryAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(AttributeGroup)
class AttributeGroupAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Attribute)
class AttributeAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'slug', 'group', 'filterable', 'sort_order')
    list_filter = ('filterable', 'group')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('group',)
    inlines = [AttributeValueInline]


@admin.register(AttributeValue)
class AttributeValueAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('value', 'attribute', 'slug', 'sort_order')
    list_filter = ('attribute',)
    search_fields = ('value', 'slug')
    autocomplete_fields = ('attribute',)


@admin.register(ProductFamily)
class ProductFamilyAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'slug', 'brand')
    search_fields = ('name', 'slug', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline]


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
        'family',
        'color_code',
    )
    search_fields = ('name', 'name_ru', 'sku', 'brand', 'color_label')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category', 'family')
    inlines = [ProductImageInline, ProductAttributeInline]
    list_editable = ('stock', 'is_active', 'is_hit', 'is_new')
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
                    'family',
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
                    'og_image',
                ),
            },
        ),
    )

    class Media:
        css = {'all': ('css/admin/lang_tabs.css',)}
        js = ('js/admin/lang_tabs.js',)


@admin.register(ProductImage)
class ProductImageAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('preview', 'product', 'sort_order', 'is_primary', 'alt')
    list_filter = ('is_primary',)
    search_fields = ('product__name', 'product__sku', 'alt')
    readonly_fields = ('preview',)

    @admin.display(description='Превʼю')
    def preview(self, obj):
        if obj.image:
            try:
                return format_html(
                    '<img src="{}" alt="" style="max-width:80px;max-height:80px;'
                    'object-fit:cover;border-radius:6px">',
                    obj.image.url,
                )
            except Exception:
                return '—'
        return '—'
