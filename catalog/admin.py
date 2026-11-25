from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from pages.admin_image_preview import admin_image_preview
from pages.admin_mixins import DefaultActiveTrueFilterMixin, TopDropdownFiltersMixin
from pages.admin_site_content_widgets import CmsTinyMCEWidget
from pages.legal_body import sanitize_legal_html

from . import admin_family  # noqa: F401
from .admin_category_nav import (
    CategoryAdminForm,
    CategoryTreeMixin,
    CategoryTreeReturnMixin,
)
from .admin_parent_cascade import CategoryParentCascadeWidget
from .admin_filter_nav import (
    FilterTreeMixin,
    FilterTreeReturnMixin,
    FilterValuesNavMixin,
    _hub_url,
)
from .admin_product_actions import PRODUCT_ACTIONS
from .admin_product_filters import ProductAdminForm, spec_fieldset_fields
from .models import (
    Attribute,
    AttributeGroup,
    AttributeValue,
    Category,
    Product,
    ProductImage,
)


class AttributeValueInline(TabularInline):
    model = AttributeValue
    extra = 1
    tab = True
    verbose_name = 'Значення фільтра'
    verbose_name_plural = 'Значення фільтрів'
    readonly_fields = ('slug',)
    fields = ('value', 'value_ru', 'slug', 'sort_order')


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


@admin.register(Category)
class CategoryAdmin(
    CategoryTreeMixin, CategoryTreeReturnMixin, TopDropdownFiltersMixin, ModelAdmin
):
    form = CategoryAdminForm
    list_display = (
        'logo_thumb',
        'name',
        'slug',
        'parent',
        'sort_order',
        'is_active',
        'show_in_menu',
    )
    list_filter = ('is_active', 'show_in_menu', 'parent')
    search_fields = ('name', 'name_ru', 'slug')
    readonly_fields = ('slug', 'logo_preview')
    fieldsets = (
        (
            'Основне',
            {
                'classes': ('tab',),
                'fields': (
                    'name',
                    'name_ru',
                    'slug',
                    'parent',
                    'logo_preview',
                    'logo',
                    'icon',
                    'home_subtitle',
                    'home_subtitle_ru',
                    'sort_order',
                    'is_active',
                    'show_in_menu',
                ),
            },
        ),
        (
            'Підказка на картці товару',
            {
                'classes': ('tab',),
                'description': (
                    'Кнопка і текст біля розміру на всіх товарах цієї категорії '
                    'або підкатегорії. Порожнє поле береться з батьківської.'
                ),
                'fields': (
                    'measure_title',
                    'measure_title_ru',
                    'measure_text',
                    'measure_text_ru',
                ),
            },
        ),
    )

    class Media:
        css = {
            'all': (
                'css/admin/lang_tabs.css',
                'css/admin/category_parent_cascade.css',
            )
        }
        js = (
            'js/admin/lang_tabs.js',
            'js/admin/category_parent_cascade.js',
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            kwargs['widget'] = CategoryParentCascadeWidget()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='')
    def logo_thumb(self, obj):
        return admin_image_preview(getattr(obj, 'logo', None), max_size=40)

    @admin.display(description='Превʼю логотипу')
    def logo_preview(self, obj):
        return admin_image_preview(getattr(obj, 'logo', None), max_size=96)


@admin.register(AttributeGroup)
class AttributeGroupAdmin(FilterTreeReturnMixin, TopDropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    search_fields = ('name', 'name_ru', 'slug')
    readonly_fields = ('slug',)
    fields = ('name', 'name_ru', 'slug', 'sort_order')
    show_add_link = False

    def get_changeform_initial_data(self, request):
        from .filter_sort import next_sort_order

        initial = super().get_changeform_initial_data(request)
        initial['sort_order'] = next_sort_order(AttributeGroup.objects.all())
        return initial

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect

        return redirect(_hub_url())

    class Media:
        css = {'all': ('css/admin/lang_tabs.css',)}
        js = ('js/admin/lang_tabs.js',)


@admin.register(Attribute)
class AttributeAdmin(
    FilterTreeMixin, FilterTreeReturnMixin, TopDropdownFiltersMixin, ModelAdmin
):
    list_display = ('name', 'slug', 'group', 'filterable', 'sort_order')
    list_filter = ('filterable', 'group')
    search_fields = ('name', 'name_ru', 'slug')
    autocomplete_fields = ('group',)
    readonly_fields = ('slug',)
    inlines = [AttributeValueInline]
    fields = ('name', 'name_ru', 'slug', 'group', 'filterable', 'sort_order')
    show_add_link = False

    class Media:
        css = {
            'all': (
                'css/admin/lang_tabs.css',
                'css/admin/filter_values_nav.css',
            )
        }
        js = ('js/admin/lang_tabs.js',)


@admin.register(AttributeValue)
class AttributeValueAdmin(
    FilterValuesNavMixin, FilterTreeReturnMixin, TopDropdownFiltersMixin, ModelAdmin
):
    list_display = ('value', 'attribute', 'slug', 'sort_order')
    list_filter = ()
    search_fields = ('value', 'value_ru', 'slug')
    autocomplete_fields = ('attribute',)
    readonly_fields = ('slug',)
    fields = ('attribute', 'value', 'value_ru', 'slug', 'sort_order')
    show_add_link = False

    class Media:
        css = {
            'all': (
                'css/admin/lang_tabs.css',
                'css/admin/filter_values_nav.css',
            )
        }
        js = ('js/admin/lang_tabs.js',)


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
        'color_code',
    )
    search_fields = ('name', 'name_ru', 'sku', 'brand', 'color_label')
    autocomplete_fields = ('category',)
    readonly_fields = ('slug', 'og_preview', 'created_at', 'updated_at')
    inlines = [ProductImageInline]
    form = ProductAdminForm
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
                    'price',
                    'old_price',
                    'stock',
                    'catalog_order',
                    'is_active',
                    'is_hit',
                    'is_new',
                    'color_code',
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
        css = {
            'all': (
                'css/admin/lang_tabs.css',
                'css/admin/product_filters.css',
            )
        }
        js = ('js/admin/lang_tabs.js', 'js/admin/product_spec_filters.js')

    def get_form(self, request, obj=None, change=False, **kwargs):
        from django.contrib.admin.utils import flatten_fieldsets

        kwargs['fields'] = flatten_fieldsets(self.fieldsets)
        return super().get_form(request, obj, change, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(self.fieldsets)
        spec_fields = spec_fieldset_fields()
        if spec_fields:
            fieldsets.append(
                (
                    'Характеристики',
                    {
                        'classes': ('tab',),
                        'description': (
                            'Кожен фільтр — список уже створених значень. '
                            'Нові варіанти додавайте в «Фільтри».'
                        ),
                        'fields': spec_fields,
                    },
                )
            )
        return fieldsets

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in {'description', 'description_ru'}:
            kwargs['widget'] = CmsTinyMCEWidget(
                attrs={'rows': 18, 'class': 'cms-tinymce--tall'}
            )
            kwargs['help_text'] = (
                'Заголовки, абзаци, списки — як на сторінці товару.'
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.description = sanitize_legal_html(obj.description)
        obj.description_ru = sanitize_legal_html(obj.description_ru)
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        from .admin_product_filters import apply_product_spec_fields

        apply_product_spec_fields(form.instance, form.cleaned_data)

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

    def get_changeform_initial_data(self, request):
        from .filter_sort import next_sort_order

        initial = super().get_changeform_initial_data(request)
        product_id = (request.GET.get('product') or '').strip()
        if product_id.isdigit():
            siblings = ProductImage.objects.filter(product_id=int(product_id))
        else:
            siblings = ProductImage.objects.none()
        initial['sort_order'] = next_sort_order(siblings)
        return initial
