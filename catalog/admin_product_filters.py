"""Одна вкладка характеристик: випадаючий список на кожен фільтр."""

import re

from django import forms
from django.db.models import Count
from unfold.widgets import UnfoldAdminSelectWidget

from .admin_parent_cascade import (
    CategoryParentCascadeWidget,
    build_parent_cascade_tree,
)
from .category_tree import cylinder_category_ids, product_needs_core_color
from .models import Attribute, AttributeValue, Product, ProductAttribute

SPEC_FIELD_PREFIX = 'spec_attr_'
SKIP_SPEC_SLUGS = frozenset({'sku-attr'})
RATING_CHOICES = tuple((n, f'{n}.0') for n in range(1, 6))


def spec_field_name(attr_pk):
    return f'{SPEC_FIELD_PREFIX}{attr_pk}'


def product_spec_attributes():
    return (
        Attribute.objects.select_related('group')
        .exclude(slug__in=SKIP_SPEC_SLUGS)
        .annotate(_value_count=Count('values'))
        .filter(_value_count__gt=0)
        .order_by('group__sort_order', 'sort_order', 'name')
    )


def spec_fieldset_fields():
    return tuple(spec_field_name(attr.pk) for attr in product_spec_attributes())


def add_spec_fields(form, product):
    selected = {}
    if getattr(product, 'pk', None):
        rows = product.product_attributes.select_related('attribute_value')
        for row in rows:
            attr_id = row.attribute_value.attribute_id
            selected.setdefault(attr_id, row.attribute_value_id)
    value_qs = AttributeValue.objects.order_by('sort_order', 'value')
    for attr in product_spec_attributes():
        name = spec_field_name(attr.pk)
        group_name = attr.group.name if attr.group_id else 'Інше'
        field = forms.ModelChoiceField(
            queryset=value_qs.filter(attribute=attr),
            required=False,
            label=attr.name,
            empty_label='Не обрано',
            widget=UnfoldAdminSelectWidget(
                attrs={
                    'data-filter-group': group_name,
                }
            ),
        )
        field.label_from_instance = lambda obj: obj.value
        if attr.pk in selected:
            field.initial = selected[attr.pk]
        form.fields[name] = field


def apply_product_spec_fields(product, cleaned_data):
    attrs = {attr.pk: attr for attr in product_spec_attributes()}
    changed = []
    for field_name, raw in cleaned_data.items():
        if not field_name.startswith(SPEC_FIELD_PREFIX):
            continue
        try:
            attr_id = int(field_name[len(SPEC_FIELD_PREFIX) :])
        except ValueError:
            continue
        attr = attrs.get(attr_id)
        if not attr:
            continue
        value = raw if isinstance(raw, AttributeValue) else None
        _replace_attr_value(product, attr, value)
        changed.extend(_sync_product_field(product, attr, value))
    if changed:
        product.save(update_fields=sorted(set(changed)))


def _replace_attr_value(product, attr, value):
    qs = ProductAttribute.objects.filter(
        product=product, attribute_value__attribute=attr
    )
    if value is None:
        qs.delete()
        return
    qs.exclude(attribute_value=value).delete()
    ProductAttribute.objects.get_or_create(product=product, attribute_value=value)


def _sync_product_field(product, attr, value):
    text = (value.value if value is not None else '').strip()
    slug = attr.slug
    if slug == 'cover' and text:
        product.cover = text
        return ['cover']
    if slug == 'brand' and text:
        product.brand = text
        return ['brand']
    if slug == 'length' and text:
        size_mm = _parse_int(text)
        if size_mm:
            product.size_mm = size_mm
            return ['size_mm']
    if slug == 'size-ab' and text:
        size_a, size_b = _parse_ab(text)
        if size_a and size_b:
            product.size_a = size_a
            product.size_b = size_b
            return ['size_a', 'size_b']
    return []


def _parse_int(text):
    match = re.search(r'(\d+)', text or '')
    return int(match.group(1)) if match else None


def _parse_ab(text):
    match = re.search(r'(\d+)\s*[×xX*]\s*(\d+)', text or '')
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ('family',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_spec_fields(self, self.instance)
        category = self.fields.get('category')
        if category is not None:
            category.widget = CategoryParentCascadeWidget(
                tree=build_parent_cascade_tree(),
                allow_empty=False,
            )
            category.help_text = (
                'Корінь, далі підкатегорія, далі листок — як у меню каталогу.'
            )
        color = self.fields.get('color_code')
        if color is not None and self.instance.pk and not product_needs_core_color(
            self.instance
        ):
            self.fields.pop('color_code')
        elif color is not None:
            color.help_text = (
                'Лише для циліндрів. Кружечки на сторінці товару та в кошику.'
            )
            color.widget.attrs['data-cylinder-ids'] = ','.join(
                str(pk) for pk in sorted(cylinder_category_ids())
            )
        rating = self.fields.get('rating')
        if rating is not None:
            self.fields['rating'] = forms.TypedChoiceField(
                label=rating.label,
                choices=RATING_CHOICES,
                coerce=int,
                required=True,
                help_text='Зірки в картці цього товару на сайті.',
                widget=UnfoldAdminSelectWidget(),
            )
        reviews = self.fields.get('reviews_count')
        if reviews is not None:
            reviews.help_text = 'Біля зірок. 0 — рядок відгуків ховається.'
        warranty = self.fields.get('warranty_months')
        if warranty is not None:
            warranty.help_text = '0 — не показувати гарантію на картці.'
