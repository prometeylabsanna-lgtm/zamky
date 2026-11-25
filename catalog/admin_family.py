from django import forms
from django.contrib import admin
from django.db.models import Count
from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import UnfoldAdminSelect2MultipleWidget

from pages.admin_image_preview import admin_image_preview
from pages.admin_mixins import TopDropdownFiltersMixin

from .models import FamilyColorSwatch, Product, ProductFamily


class FamilyColorSwatchInline(TabularInline):
    model = FamilyColorSwatch
    extra = 0
    max_num = 3
    fields = ('preview', 'color_code', 'image')
    readonly_fields = ('preview',)
    verbose_name = 'Плашка кольору'
    verbose_name_plural = 'Плашки кольорів'

    @admin.display(description='Превʼю')
    def preview(self, obj):
        return admin_image_preview(getattr(obj, 'image', None), max_size=72)


class ProductFamilyForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.none(),
        required=False,
        label='Варіанти',
        help_text=(
            'Окремі товари (артикули) цієї моделі. '
            'Кожен — свій колір і розмір. На картці товару сімʼя не показується.'
        ),
        widget=UnfoldAdminSelect2MultipleWidget,
    )

    class Meta:
        model = ProductFamily
        fields = ('name', 'slug', 'brand', 'short_description', 'description')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Product.objects.order_by('name', 'sku')
        self.fields['products'].queryset = qs
        self.fields['products'].label_from_instance = (
            lambda obj: f'{obj.sku} — {obj.name}'
        )
        if self.instance.pk:
            self.fields['products'].initial = qs.filter(family=self.instance)


def _sync_family_products(family, selected):
    selected_ids = list(selected.values_list('pk', flat=True))
    Product.objects.filter(family=family).exclude(pk__in=selected_ids).update(
        family=None
    )
    if selected_ids:
        Product.objects.filter(pk__in=selected_ids).update(family=family)


@admin.register(ProductFamily)
class ProductFamilyAdmin(TopDropdownFiltersMixin, ModelAdmin):
    form = ProductFamilyForm
    list_display = ('name', 'brand', 'variant_count')
    search_fields = ('name', 'brand', 'slug')
    readonly_fields = ('slug',)
    inlines = [FamilyColorSwatchInline]
    fieldsets = (
        (
            'Основне',
            {
                'fields': (
                    'name',
                    'slug',
                    'brand',
                    'short_description',
                    'description',
                ),
            },
        ),
        (
            'Варіанти',
            {
                'description': (
                    'Зберіть сюди товари однієї моделі. '
                    'Плашки кольорів — фото кнопок на сторінці товару.'
                ),
                'fields': ('products',),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_n=Count('variants'))

    @admin.display(description='Варіантів')
    def variant_count(self, obj):
        return getattr(obj, '_n', obj.variants.count())

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        selected = form.cleaned_data.get('products')
        if selected is None:
            return
        _sync_family_products(form.instance, selected)
