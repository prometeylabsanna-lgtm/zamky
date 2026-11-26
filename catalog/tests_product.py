from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from catalog.measure_guide import (
    MEASURE_TEXT_RU,
    MEASURE_TEXT_UA,
    MEASURE_TITLE_RU,
    MEASURE_TITLE_UA,
)
from catalog.models import (
    Attribute,
    AttributeGroup,
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductFamily,
)
from orders.models import QuickOrder


class ProductPageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(
            name='Циліндри',
            slug='cylinders',
            measure_title=MEASURE_TITLE_UA,
            measure_title_ru=MEASURE_TITLE_RU,
            measure_text=MEASURE_TEXT_UA,
            measure_text_ru=MEASURE_TEXT_RU,
        )
        self.family = ProductFamily.objects.create(
            name='ABARO B100',
            slug='abaro-b100',
            brand='ABARO',
            description='Абзац один.\n\nАбзац два.\n\nАбзац три.',
        )
        group = AttributeGroup.objects.create(name='Загальне', slug='zagalne', sort_order=1)
        brand_attr = Attribute.objects.create(
            name='Бренд', slug='brand', group=group, filterable=True, sort_order=1
        )
        self.av_brand = AttributeValue.objects.create(attribute=brand_attr, value='ABARO', slug='abaro')

        self.variants = []
        for color, label, add in (('G', 'Латунь', 0), ('N', 'Нікель', 40)):
            for size, a, b, base in ((60, 30, 30, 400), (70, 35, 35, 460)):
                price = Decimal(str(base + add))
                old = Decimal(str(round(float(price) * 1.3 / 10) * 10))
                sku = f'ABR-B100-{size}-{color}'
                p = Product.objects.create(
                    category=self.cat,
                    family=self.family,
                    name=f'Циліндр ABARO B100 {size} ({a}*{b}) {label}',
                    slug=sku.lower(),
                    sku=sku,
                    price=price,
                    old_price=old,
                    stock=20 if color == 'G' else 3,
                    brand='ABARO',
                    color_code=color,
                    color_label=label,
                    cover='Полірована латунь' if color == 'G' else 'Матовий нікель',
                    size_mm=size,
                    size_a=a,
                    size_b=b,
                    description=self.family.description,
                )
                ProductAttribute.objects.create(product=p, attribute_value=self.av_brand)
                self.variants.append(p)
        self.product = self.variants[0]

    def tearDown(self):
        translation.deactivate_all()

    def test_product_page_ok(self):
        response = self.client.get(reverse('catalog:product', args=[self.product.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Колір серцевини')
        body = response.content.decode()
        self.assertLess(body.index('pdp-cart-btn'), body.index('Колір серцевини'))
        self.assertContains(response, 'Як виміряти циліндр?')
        self.assertContains(response, 'Швидке замовлення в 1 клік')
        self.assertContains(response, 'data-pdp-tabs')
        self.assertNotContains(response, 'pdp-specs__group')
        self.assertContains(response, self.product.sku)
        self.assertContains(response, 'Гарантія 12 місяців')
        self.assertNotContains(response, '· 0')
        self.assertContains(response, '>Відгуки</button>')

    def test_product_reviews_and_warranty_from_fields(self):
        self.product.reviews_count = 2
        self.product.warranty_months = 24
        self.product.save(update_fields=['reviews_count', 'warranty_months'])
        page = self.client.get(reverse('catalog:product', args=[self.product.slug]))
        self.assertContains(page, '· 2 відгуки')
        self.assertContains(page, 'Гарантія 24 місяці')

    def test_variant_context(self):
        response = self.client.get(reverse('catalog:product', args=[self.product.slug]))
        colors = response.context['variant_colors']
        sizes = response.context['variant_sizes']
        self.assertEqual(len(colors), 2)
        self.assertEqual(len(sizes), 2)
        self.assertIn('Нікель', [c['label'] for c in colors])

    def test_solo_product_shows_core_color(self):
        solo = Product.objects.create(
            category=self.cat,
            name='тест',
            slug='product-solo-color',
            sku='64675474-solo',
            price=Decimal('100'),
            color_code='B',
            size_mm=22,
            size_a=25,
            size_b=26,
        )
        response = self.client.get(reverse('catalog:product', args=[solo.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Колір серцевини')
        body = response.content.decode()
        self.assertLess(body.index('pdp-cart-btn'), body.index('Колір серцевини'))
        self.assertContains(response, 'Чорний')
        colors = response.context['variant_colors']
        self.assertEqual(len(colors), 1)
        self.assertEqual(colors[0]['code'], 'B')
        self.assertEqual(len(response.context['variant_sizes']), 1)

    def test_measure_from_parent_category(self):
        parent = Category.objects.create(
            name='Батько',
            slug='parent-measure',
            measure_title='Кнопка батька',
            measure_text='Текст батька',
        )
        child = Category.objects.create(name='Дитина', slug='child-measure', parent=parent)
        solo = Product.objects.create(
            category=child,
            name='дочірній',
            slug='child-measure-p',
            sku='CHILD-M-1',
            price=Decimal('10'),
            size_mm=60,
            size_a=30,
            size_b=30,
        )
        page = self.client.get(reverse('catalog:product', args=[solo.slug]))
        self.assertContains(page, 'Кнопка батька')
        self.assertContains(page, 'Текст батька')

    def test_measure_hidden_when_empty(self):
        empty = Category.objects.create(name='Замки', slug='locks-no-measure')
        solo = Product.objects.create(
            category=empty,
            name='замок',
            slug='lock-no-measure',
            sku='LOCK-M-1',
            price=Decimal('10'),
            size_mm=60,
            size_a=30,
            size_b=30,
        )
        page = self.client.get(reverse('catalog:product', args=[solo.slug]))
        self.assertNotContains(page, 'Як виміряти циліндр?')
        self.assertNotContains(page, 'data-toggle-guide')

    def test_measure_ru(self):
        page = self.client.get(f'/ru/product/{self.product.slug}/')
        self.assertContains(page, 'Как измерить цилиндр?')
        self.assertContains(page, 'Измерьте расстояние')

    def test_description_keeps_lists(self):
        self.product.description = (
            '<p>Повний опис товару</p><ul><li>список1</li><li>список2</li></ul>'
        )
        self.product.save()
        page = self.client.get(reverse('catalog:product', args=[self.product.slug]))
        self.assertContains(page, 'Повний опис товару')
        self.assertContains(page, '<li>список1</li>')
        self.assertContains(page, '<li>список2</li>')
        self.assertNotContains(page, 'список1 список2')

    def test_spec_rows_flat_like_mockup(self):
        sizes = AttributeGroup.objects.create(name='Розміри', slug='rozmiry', sort_order=2)
        size_ab = Attribute.objects.create(
            name='Розмір A×B', slug='size-ab', group=sizes, filterable=False
        )
        fake_ab = AttributeValue.objects.create(
            attribute=size_ab, value='45×45 мм', slug='45x45'
        )
        ProductAttribute.objects.create(product=self.product, attribute_value=fake_ab)
        filters = AttributeGroup.objects.create(name='Фільтри', slug='filters', sort_order=10)
        country = Attribute.objects.create(
            name='Країна виробництва', slug='country', group=filters, sort_order=1
        )
        av_country = AttributeValue.objects.create(
            attribute=country, value='Україна', slug='ua'
        )
        ProductAttribute.objects.create(product=self.product, attribute_value=av_country)

        response = self.client.get(reverse('catalog:product', args=[self.product.slug]))
        rows = response.context['spec_rows']
        keys = [r['k'] for r in rows]
        self.assertEqual(keys[:3], ['Бренд', 'Країна виробництва', 'Категорія'])
        self.assertEqual(keys.count('Бренд'), 1)
        by_key = {r['k']: r for r in rows}
        self.assertEqual(by_key['Бренд']['v'], 'ABARO')
        self.assertEqual(by_key['Категорія']['v'], 'Циліндри')
        self.assertEqual(by_key['Артикул']['v'], self.product.sku)
        self.assertEqual(by_key['Артикул']['spec'], 'sku')
        self.assertEqual(by_key['Гарантія']['v'], '12 місяців')
        self.assertEqual(by_key['Розмір A×B']['v'], '30×30 мм')
        self.assertEqual(by_key['Загальна довжина']['v'], '60 мм')
        self.assertEqual(by_key['Покриття']['v'], 'Полірована латунь')
        self.assertNotIn('45×45 мм', {r['v'] for r in rows})
        self.assertLess(keys.index('Артикул'), keys.index('Гарантія'))
        self.assertNotContains(response, '>Фільтри<')
        self.assertContains(response, 'data-spec-sku')
        self.assertContains(response, 'data-spec-ab')
        self.assertContains(response, 'data-spec-len')
        self.assertContains(response, 'data-spec-cover')

    def test_spec_groups_russian(self):
        safety = AttributeGroup.objects.create(
            name='Безпека та комплектація',
            name_ru='Безопасность и комплектация',
            slug='bezpeka-ta-komplektatsiia',
            sort_order=4,
        )
        keys = Attribute.objects.create(
            name='Кількість ключів',
            name_ru='Количество ключей',
            slug='keys',
            group=safety,
            filterable=False,
        )
        av_keys = AttributeValue.objects.create(
            attribute=keys, value='5', value_ru='5', slug='5-keys'
        )
        ProductAttribute.objects.create(product=self.product, attribute_value=av_keys)
        page = self.client.get(f'/ru/product/{self.product.slug}/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Количество ключей')
        self.assertContains(page, 'Общая длина')
        self.assertNotContains(page, 'Безопасность и комплектация')

    def test_color_code_sets_label(self):
        self.product.color_code = 'N'
        self.product.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.color_label, 'Нікель')
        self.product.color_code = ''
        self.product.color_label = 'чорний'
        self.product.description = 'Звичайний текст'
        self.product.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.color_label, 'чорний')
        self.assertEqual(self.product.description, 'Звичайний текст')

    def test_add_to_cart_with_quantity(self):
        url = reverse('cart:add', args=[self.product.pk])
        response = self.client.post(url, {'quantity': 3}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart[str(self.product.pk)]['qty'], 3)

    def test_quick_order(self):
        url = reverse('orders:quick', args=[self.product.pk])
        response = self.client.post(
            url,
            {'phone': '67 000 00 00', 'quantity': 2},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Дякуємо')
        qo = QuickOrder.objects.get()
        self.assertEqual(qo.product_id, self.product.pk)
        self.assertEqual(qo.quantity, 2)
        self.assertTrue(qo.phone.startswith('+380'))


class ProductAdminColorTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            'padmin', 'p@example.com', 'pass12345'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.cat = Category.objects.create(name='Циліндри', slug='cyl-admin')
        self.product = Product.objects.create(
            category=self.cat,
            name='Test color',
            slug='test-color-admin',
            sku='TST-COLOR',
            price=Decimal('100'),
            color_code='G',
        )

    def tearDown(self):
        translation.deactivate_all()

    def test_admin_category_cascade(self):
        url = reverse('admin:catalog_product_change', args=[self.product.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'data-parent-cascade')
        self.assertContains(page, 'data-cascade-required')
        self.assertContains(page, 'data-cascade-toggle')
        self.assertContains(page, 'data-cascade-col="3"')
        self.assertNotContains(page, 'admin-autocomplete')

    def test_admin_color_dropdown(self):
        url = reverse('admin:catalog_product_change', args=[self.product.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Колір серцевини')
        self.assertContains(page, '>Латунь<')
        self.assertContains(page, '>Нікель<')
        self.assertContains(page, '>Чорний<')
        self.assertNotContains(page, 'Код кольору')

    def test_admin_hides_core_color_outside_cylinders(self):
        locks = Category.objects.create(name='Замки', slug='locks-admin-color')
        other = Product.objects.create(
            category=locks,
            name='Замок без серцевини',
            slug='lock-no-core',
            sku='LOCK-NO-CORE',
            price=Decimal('200'),
        )
        page = self.client.get(
            reverse('admin:catalog_product_change', args=[other.pk])
        )
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'id="id_color_code"')
        self.assertNotContains(page, 'Колір серцевини')

    def test_admin_description_tinymce(self):
        url = reverse('admin:catalog_product_change', args=[self.product.pk])
        page = self.client.get(url)
        self.assertContains(page, 'cms-tinymce')
        self.assertNotContains(page, 'Короткий опис')

    def test_admin_product_fields_and_attrs(self):
        group = AttributeGroup.objects.create(name='Безпека', slug='bezpeka', sort_order=4)
        keys = Attribute.objects.create(
            name='Кількість ключів', slug='keys', group=group, filterable=False
        )
        AttributeValue.objects.create(attribute=keys, value='5', slug='5')
        sku_attr = Attribute.objects.create(
            name='Артикул', slug='sku-attr', group=group, filterable=False
        )
        empty = Attribute.objects.create(
            name='новий', slug='empty-filter', filterable=True
        )
        url = reverse('admin:catalog_product_change', args=[self.product.pk])
        page = self.client.get(url)
        self.assertContains(page, f'name="spec_attr_{keys.pk}"')
        self.assertContains(page, f'list="spec-values-{keys.pk}"')
        self.assertNotContains(page, 'data-filter-group')
        self.assertContains(page, 'Кількість ключів')
        self.assertContains(page, '<option value="5">')
        self.assertNotContains(page, 'Оздоблення')
        self.assertNotContains(page, 'data-attr-master')
        self.assertNotContains(page, f'name="spec_attr_{sku_attr.pk}"')
        self.assertContains(page, f'name="spec_attr_{empty.pk}"')
        self.assertContains(page, 'name="rating"')
        self.assertContains(page, 'Рейтинг')
        self.assertContains(page, 'name="reviews_count"')
        self.assertContains(page, 'name="warranty_months"')
        self.assertNotContains(page, 'id="id_cover"')
        self.assertNotContains(page, 'id="id_size_mm"')
        self.assertNotContains(page, 'id="id_family"')

    def test_apply_spec_fields_syncs_size(self):
        from catalog.admin_product_filters import apply_product_spec_fields, spec_field_name

        sizes = AttributeGroup.objects.create(name='Розміри', slug='rozmiry', sort_order=2)
        length = Attribute.objects.create(
            name='Загальна довжина', slug='length', group=sizes, filterable=False
        )
        av = AttributeValue.objects.create(attribute=length, value='70 мм', slug='70-mm')
        apply_product_spec_fields(self.product, {spec_field_name(length.pk): av})
        self.product.refresh_from_db()
        self.assertEqual(self.product.size_mm, 70)
        self.assertTrue(
            ProductAttribute.objects.filter(
                product=self.product, attribute_value=av
            ).exists()
        )

    def test_apply_spec_fields_creates_new_value(self):
        from catalog.admin_product_filters import apply_product_spec_fields, spec_field_name

        country = Attribute.objects.create(name='Країна виробництва', slug='country')
        AttributeValue.objects.create(attribute=country, value='Україна', slug='ua')
        apply_product_spec_fields(self.product, {spec_field_name(country.pk): ' україна '})
        self.assertEqual(AttributeValue.objects.filter(attribute=country).count(), 1)
        apply_product_spec_fields(self.product, {spec_field_name(country.pk): 'Італія'})
        values = set(
            self.product.attributes.filter(attribute=country).values_list('value', flat=True)
        )
        self.assertEqual(values, {'Італія'})
        self.assertEqual(AttributeValue.objects.filter(attribute=country).count(), 2)
        apply_product_spec_fields(self.product, {spec_field_name(country.pk): ''})
        self.assertFalse(self.product.attributes.filter(attribute=country).exists())
        self.assertEqual(AttributeValue.objects.filter(attribute=country).count(), 2)

    def test_filter_groups_in_admin_nav(self):
        from django.conf import settings
        from django.test import RequestFactory

        from config.settings.base import _admin_nav_active

        nav = settings.UNFOLD['SIDEBAR']['navigation']
        catalog = next(g for g in nav if g.get('title') == 'Каталог')
        titles = [item['title'] for item in catalog['items']]
        self.assertIn('Характеристики', titles)
        self.assertIn('Сімʼї', titles)
        self.assertNotIn('Групи фільтрів', titles)
        self.assertNotIn('Значення фільтрів', titles)
        factory = RequestFactory()
        attr_active = _admin_nav_active('catalog/attribute/')
        group_active = _admin_nav_active('catalog/attributegroup/')
        on_attr = factory.get('/admin/catalog/attribute/')
        on_group = factory.get('/admin/catalog/attributegroup/')
        self.assertTrue(attr_active(on_attr))
        self.assertFalse(group_active(on_attr))
        self.assertTrue(group_active(on_group))
        self.assertFalse(attr_active(on_group))
        page = self.client.get(reverse('admin:catalog_attribute_changelist'))
        self.assertContains(page, 'Додати характеристику')
        self.assertNotContains(page, 'Додати групу')
        groups = self.client.get(reverse('admin:catalog_attributegroup_changelist'))
        self.assertEqual(groups.status_code, 302)

    def test_category_admin_measure_fields(self):
        url = reverse('admin:catalog_category_change', args=[self.cat.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Підказка на картці товару')
        self.assertContains(page, 'id_measure_title')
        self.assertContains(page, 'id_measure_text')


class FilterValuesNavTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            'fnav', 'fn@example.com', 'pass12345'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.group = AttributeGroup.objects.create(name='Розміри', slug='rozmiry-nav')
        self.attr = Attribute.objects.create(
            name='Розмір A×B', slug='size-ab-nav', group=self.group
        )
        AttributeValue.objects.create(
            attribute=self.attr, value='30×30 мм', slug='3030-nav'
        )

    def test_groups_then_filters_then_values(self):
        hub = reverse('admin:catalog_attribute_changelist')
        values_url = reverse('admin:catalog_attributevalue_changelist')
        flat = self.client.get(hub)
        self.assertEqual(flat.status_code, 200)
        self.assertContains(flat, 'Розмір A×B')
        self.assertContains(flat, 'група: Розміри')
        self.assertContains(flat, 'Додати характеристику')
        self.assertNotContains(flat, '30×30 мм')
        old_link = self.client.get(hub, {'group': self.group.pk})
        self.assertContains(old_link, 'Розмір A×B')
        values = self.client.get(
            values_url, {'group': self.group.pk, 'attribute': self.attr.pk}
        )
        self.assertContains(values, '30×30 мм')
        self.assertContains(values, 'Додати значення')
        bounced = self.client.get(values_url)
        self.assertEqual(bounced.status_code, 302)

    def test_empty_values_add_keeps_attribute(self):
        AttributeValue.objects.filter(attribute=self.attr).delete()
        values_url = reverse('admin:catalog_attributevalue_changelist')
        page = self.client.get(
            values_url, {'group': self.group.pk, 'attribute': self.attr.pk}
        )
        add_url = reverse('admin:catalog_attributevalue_add')
        self.assertContains(page, f'{add_url}?attribute={self.attr.pk}')
        self.assertContains(page, 'Додати значення')

    def test_sort_order_starts_at_one(self):
        first = AttributeValue.objects.get(slug='3030-nav')
        self.assertEqual(first.sort_order, 1)
        second = AttributeValue.objects.create(
            attribute=self.attr, value='35×35 мм', slug='3535-nav'
        )
        self.assertEqual(second.sort_order, 2)
        kept = AttributeValue.objects.create(
            attribute=self.attr,
            value='40×40 мм',
            slug='4040-nav',
            sort_order=8,
        )
        self.assertEqual(kept.sort_order, 8)
        nxt = AttributeValue.objects.create(
            attribute=self.attr, value='45×45 мм', slug='4545-nav'
        )
        self.assertEqual(nxt.sort_order, 9)
        other_attr = Attribute.objects.create(
            name='Інший', slug='other-nav', group=self.group
        )
        other = AttributeValue.objects.create(
            attribute=other_attr, value='X', slug='x-nav'
        )
        self.assertEqual(other.sort_order, 1)

    def test_add_filter_form_uses_group_and_values(self):
        url = reverse('admin:catalog_attribute_add')
        page = self.client.get(url, {'group': self.group.pk})
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, f'value="{self.group.pk}"')
        self.assertContains(page, self.group.name)
        self.assertNotContains(page, 'name="values-0-value"')
        self.assertContains(page, self.group.name)
        self.assertNotContains(page, 'admin-autocomplete')
        self.assertNotContains(page, '_popup=1')
        self.assertNotContains(page, 'Додати ще одну Фільтр')

    def test_add_value_form_hides_attribute(self):
        url = reverse('admin:catalog_attributevalue_add')
        bounced = self.client.get(url)
        self.assertEqual(bounced.status_code, 302)
        values_url = reverse('admin:catalog_attributevalue_changelist')
        from_list = self.client.get(
            url,
            HTTP_REFERER=f'{values_url}?group={self.group.pk}&attribute={self.attr.pk}',
        )
        self.assertEqual(from_list.status_code, 200)
        page = self.client.get(url, {'attribute': self.attr.pk})
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'type="hidden"')
        self.assertContains(page, 'name="attribute"')
        self.assertContains(page, f'value="{self.attr.pk}"')
        self.assertContains(page, self.attr.name)
        self.assertContains(page, 'Характеристики')
        self.assertNotContains(page, '---------')
        self.assertNotContains(page, 'admin-autocomplete')

    def test_add_filter_opens_values_list(self):
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory

        from catalog.admin import AttributeAdmin
        from catalog.models import Attribute as Attr

        created = Attr.objects.create(
            name='Новий фільтр тест', group=self.group, sort_order=1
        )
        req = RequestFactory().post('/')
        req.user = self.user
        response = AttributeAdmin(Attr, AdminSite()).response_post_save_add(
            req, created
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'attribute={created.pk}', response['Location'])

    def test_add_value_returns_to_filter_list(self):
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory

        from catalog.admin import AttributeValueAdmin

        created = AttributeValue.objects.create(
            attribute=self.attr, value='Нове', slug='nove-nav'
        )
        req = RequestFactory().post('/')
        req.user = self.user
        response = AttributeValueAdmin(
            AttributeValue, AdminSite()
        ).response_post_save_add(req, created)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'attribute={self.attr.pk}', response['Location'])

    def test_add_value_form_initial_order(self):
        from django.contrib import admin
        from django.test import RequestFactory

        from catalog.admin import AttributeValueAdmin

        request = RequestFactory().get('/', {'attribute': str(self.attr.pk)})
        request.user = self.user
        initial = AttributeValueAdmin(
            AttributeValue, admin.site
        ).get_changeform_initial_data(request)
        self.assertEqual(initial['sort_order'], 2)
        self.assertEqual(initial['attribute'], self.attr.pk)
