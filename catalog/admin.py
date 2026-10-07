from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

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


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    tab = True


class ProductAttributeInline(TabularInline):
    model = ProductAttribute
    extra = 1
    autocomplete_fields = ('attribute_value',)
    tab = True


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


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(AttributeGroup)
class AttributeGroupAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Attribute)
class AttributeAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'group', 'filterable', 'sort_order')
    list_filter = ('filterable', 'group')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('group',)
    inlines = [AttributeValueInline]


@admin.register(AttributeValue)
class AttributeValueAdmin(ModelAdmin):
    list_display = ('value', 'attribute', 'slug', 'sort_order')
    list_filter = ('attribute',)
    search_fields = ('value', 'slug')
    autocomplete_fields = ('attribute',)


@admin.register(ProductFamily)
class ProductFamilyAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'brand')
    search_fields = ('name', 'slug', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline]


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = (
        'name',
        'sku',
        'family',
        'color_label',
        'size_mm',
        'category',
        'price',
        'stock',
        'catalog_order',
        'is_active',
        'is_hit',
        'is_new',
    )
    list_filter = ('is_active', 'is_hit', 'is_new', 'category', 'brand', 'family', 'color_code')
    search_fields = ('name', 'sku', 'brand', 'color_label')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category', 'family')
    inlines = [ProductImageInline, ProductAttributeInline]
    list_editable = ('stock', 'is_active', 'is_hit', 'is_new')


@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ('product', 'sort_order', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('product__name', 'product__sku')
