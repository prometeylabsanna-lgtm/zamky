"""Вкладка «Характеристики» товару: один рядок на характеристику.

Значення вводиться текстом з підказками з довідника; нове значення
створюється в довіднику автоматично. Групи на порядок і вигляд не впливають.
"""

import re

from django import forms
from django.db.models import Count
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldAdminTextInputWidget

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
    """Усі характеристики плоским списком (групи на порядок не впливають)."""
    return (
        Attribute.objects.exclude(slug__in=SKIP_SPEC_SLUGS)
        .annotate(_value_count=Count('values'))
        .order_by('sort_order', 'name', 'pk')
    )


def spec_fieldset_fields():
    return tuple(spec_field_name(attr.pk) for attr in product_spec_attributes())


class SpecValueWidget(UnfoldAdminTextInputWidget):
    """Текстове поле + підказки з довідника (datalist): обрати або ввести нове."""

    def __init__(self, choices=(), list_id='', attrs=None):
        attrs = {**(attrs or {}), 'autocomplete': 'off'}
        if list_id:
            attrs['list'] = list_id
        super().__init__(attrs=attrs)
        self.choices = list(choices)
        self.list_id = list_id

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        if not self.list_id:
            return html
        options = ''.join(
            format_html('<option value="{}"></option>', text) for text in self.choices
        )
        return mark_safe(
            f'{html}<datalist id="{escape(self.list_id)}">{options}</datalist>'
        )


def add_spec_fields(form, product):
    selected = {}
    if getattr(product, 'pk', None):
        rows = product.product_attributes.select_related('attribute_value')
        for row in rows:
            attr_id = row.attribute_value.attribute_id
            selected.setdefault(attr_id, row.attribute_value.value)
    values_by_attr = {}
    for attr_id, text in AttributeValue.objects.order_by(
        'sort_order', 'value'
    ).values_list('attribute_id', 'value'):
        values_by_attr.setdefault(attr_id, []).append(text)
    for attr in product_spec_attributes():
        name = spec_field_name(attr.pk)
        hint = 'Показується у фільтрах каталогу.' if attr.filterable else ''
        field = forms.CharField(
            required=False,
            max_length=200,
            label=attr.name,
            help_text=hint,
            widget=SpecValueWidget(
                choices=values_by_attr.get(attr.pk, ()),
                list_id=f'spec-values-{attr.pk}',
                attrs={'placeholder': 'Не вказано — оберіть або введіть нове'},
            ),
        )
        if attr.pk in selected:
            field.initial = selected[attr.pk]
        form.fields[name] = field


def resolve_spec_value(attr, raw):
    """Знаходить значення в довіднику (без регістру) або створює нове."""
    if isinstance(raw, AttributeValue):
        return raw
    text = ' '.join(str(raw or '').split())
    if not text:
        return None
    wanted = text.casefold()
    for existing in AttributeValue.objects.filter(attribute=attr).order_by('pk'):
        if ' '.join((existing.value or '').split()).casefold() == wanted:
            return existing
    return AttributeValue.objects.create(attribute=attr, value=text)


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
        value = resolve_spec_value(attr, raw)
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
        fields = '__all__'

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
                'Кружечок на сторінці товару. Назву можна задати окремо.'
            )
            color.widget.attrs['data-cylinder-ids'] = ','.join(
                str(pk) for pk in sorted(cylinder_category_ids())
            )
        label = self.fields.get('color_label')
        if label is not None and 'color_code' not in self.fields:
            self.fields.pop('color_label')
        elif label is not None:
            label.label = 'Назва кольору'
            label.help_text = (
                'Як покупець бачить колір. Порожнє — «Латунь», «Нікель» або «Чорний» '
                'відповідно до вибраного варіанту.'
            )
        rating = self.fields.get('rating')
        if rating is not None:
            self.fields['rating'] = forms.TypedChoiceField(
                label=rating.label,
                choices=RATING_CHOICES,
                coerce=int,
                required=True,
                help_text='Зірки на сторінці товару, поки немає активних відгуків. Коли вони є — оцінка рахується з них.',
                widget=UnfoldAdminSelectWidget(),
            )
        reviews = self.fields.get('reviews_count')
        if reviews is not None:
            reviews.help_text = 'Рахується автоматично з активних відгуків.'
        warranty = self.fields.get('warranty_months')
        if warranty is not None:
            warranty.help_text = '0 — не показувати гарантію на картці.'
        old_price = self.fields.get('old_price')
        if old_price is not None:
            old_price.help_text = (
                'Якщо заповнити — на сайті закреслена ціна, актуальна лишається в «Ціна».'
            )
        stock = self.fields.get('stock')
        if stock is not None:
            stock.help_text = '0 — товар показується як немає в наявності.'
        is_hit = self.fields.get('is_hit')
        if is_hit is not None:
            is_hit.help_text = 'Може з’явитися у вкладці «Хіти» на головній.'
        is_new = self.fields.get('is_new')
        if is_new is not None:
            is_new.help_text = (
                'Сортування «Нові» в каталозі та вкладка «Новинки» на головній.'
            )
        is_active = self.fields.get('is_active')
        if is_active is not None:
            is_active.help_text = 'Без галочки товар не видно в каталозі.'
        seo_title = self.fields.get('seo_title')
        if seo_title is not None:
            seo_title.help_text = (
                'Заголовок вкладки браузера. Порожнє — назва товару.'
            )
        seo_desc = self.fields.get('seo_description')
        if seo_desc is not None:
            seo_desc.help_text = (
                'Опис для пошуку. Порожнє — короткий опис або загальний з SEO-налаштувань.'
            )
        canonical = self.fields.get('canonical_url')
        if canonical is not None:
            canonical.help_text = (
                'Залиште порожнім, якщо не впевнені. Потрібне лише для особливої адреси сторінки.'
            )
        og = self.fields.get('og_image')
        if og is not None:
            from pages.admin_guidelines import IMAGE_HINTS

            og.help_text = (
                IMAGE_HINTS['og']
                + ' Порожнє — загальна картинка з SEO-налаштувань.'
            )
        from pages.admin_guidelines import apply_form_char_hints

        apply_form_char_hints(self)
