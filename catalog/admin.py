from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldAdminTextInputWidget

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
    _attribute_url,
    _group_key,
    _hub_url,
    bound_attribute_id,
)
from .admin_product_actions import PRODUCT_ACTIONS
from .admin_product_filters import ProductAdminForm, spec_fieldset_fields
from .category_tree import product_needs_core_color
from .models import (
    Attribute,
    AttributeGroup,
    AttributeValue,
    Category,
    Product,
    ProductImage,
)


def _plain_fk_select():
    return UnfoldAdminSelectWidget()


def _no_related_menu(field):
    widget = getattr(field, 'widget', None)
    while widget is not None:
        widget.can_add_related = False
        widget.can_change_related = False
        widget.can_delete_related = False
        widget.can_view_related = False
        widget = getattr(widget, 'widget', None)
    return field


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
        css = {
            'all': (
                'css/admin/lang_tabs.css',
                'css/admin/filter_values_nav.css',
            )
        }
        js = ('js/admin/lang_tabs.js',)


@admin.register(Attribute)
class AttributeAdmin(
    FilterTreeMixin, FilterTreeReturnMixin, TopDropdownFiltersMixin, ModelAdmin
):
    list_display = ('name', 'slug', 'group', 'filterable', 'sort_order')
    list_filter = ('filterable', 'group')
    search_fields = ('name', 'name_ru', 'slug')
    readonly_fields = ('slug',)
    fields = ('name', 'name_ru', 'filterable', 'sort_order', 'group', 'slug')
    show_add_link = False

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        labels = {
            'name': ('Назва характеристики', 'Як на сайті: «Країна виробництва», «Тип механізму».'),
            'filterable': (
                'Показувати як фільтр у каталозі',
                'Без галочки характеристика видна лише в картці товару.',
            ),
            'group': (
                'Група (необовʼязково)',
                'Лише для впорядкування в адмінці. На сайті назви груп не показуються.',
            ),
            'sort_order': ('Порядок', 'Порядок у картці товару й у фільтрах.'),
        }
        for name, (label, help_text) in labels.items():
            field = form.base_fields.get(name)
            if field is not None:
                field.label = label
                field.help_text = help_text
        group = form.base_fields.get('group')
        if group is not None:
            _no_related_menu(group)
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'group':
            kwargs['widget'] = _plain_fk_select()
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        return _no_related_menu(field)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in {'name', 'name_ru'}:
            kwargs['widget'] = UnfoldAdminTextInputWidget(
                attrs={'autocomplete': 'off'}
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def response_post_save_add(self, request, obj):
        return HttpResponseRedirect(_attribute_url(_group_key(obj.group), obj.pk))

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
    readonly_fields = ('slug',)
    fields = ('attribute', 'value', 'value_ru', 'slug', 'sort_order')
    show_add_link = False

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in {'value', 'value_ru'}:
            kwargs['widget'] = UnfoldAdminTextInputWidget(
                attrs={'autocomplete': 'off'}
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        if request.method == 'GET' and bound_attribute_id(request) is None:
            return HttpResponseRedirect(_hub_url())
        return super().add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        attr_id = bound_attribute_id(request, obj)
        if attr_id:
            obj.attribute_id = attr_id
        super().save_model(request, obj, form, change)

    def response_post_save_add(self, request, obj):
        return HttpResponseRedirect(
            _attribute_url(_group_key(obj.attribute.group), obj.attribute_id)
        )

    def response_post_save_change(self, request, obj):
        return HttpResponseRedirect(
            _attribute_url(_group_key(obj.attribute.group), obj.attribute_id)
        )

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        field = form.base_fields.get('attribute')
        attr_id = bound_attribute_id(request, obj)
        if field is not None and attr_id:
            field.widget = forms.HiddenInput()
            field.initial = attr_id
            field.label = ''
            field.help_text = ''
        elif field is not None:
            _no_related_menu(field)
        return form

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
                    'rating',
                    'reviews_count',
                    'warranty_months',
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
                'css/admin/category_parent_cascade.css',
            )
        }
        js = (
            'js/admin/lang_tabs.js',
            'js/admin/category_parent_cascade.js',
            'js/admin/product_core_color.js',
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            kwargs['widget'] = CategoryParentCascadeWidget(allow_empty=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        from django.contrib.admin.utils import flatten_fieldsets

        kwargs['fields'] = flatten_fieldsets(self.fieldsets)
        return super().get_form(request, obj, change, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = []
        for title, opts in self.fieldsets:
            opts = dict(opts)
            fields = tuple(opts.get('fields', ()))
            if obj is not None and not product_needs_core_color(obj):
                fields = tuple(name for name in fields if name != 'color_code')
            opts['fields'] = fields
            fieldsets.append((title, opts))
        spec_fields = spec_fieldset_fields()
        if spec_fields:
            fieldsets.append(
                (
                    'Характеристики',
                    {
                        'classes': ('tab', 'product-specs-tab'),
                        'description': (
                            'Одна характеристика — один рядок. Почніть вводити значення: '
                            'оберіть з підказок або впишіть нове — його буде додано '
                            'в довідник «Характеристики». Порожнє поле — не показувати.'
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
