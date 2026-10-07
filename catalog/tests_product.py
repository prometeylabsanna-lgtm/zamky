from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

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
        self.cat = Category.objects.create(name='Циліндри', slug='cylinders')
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

    def test_product_page_ok(self):
        response = self.client.get(reverse('catalog:product', args=[self.product.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Колір серцевини')
        self.assertContains(response, 'Як виміряти циліндр?')
        self.assertContains(response, 'Швидке замовлення в 1 клік')
        self.assertContains(response, 'Загальне')
        self.assertContains(response, self.product.sku)

    def test_variant_context(self):
        response = self.client.get(reverse('catalog:product', args=[self.product.slug]))
        colors = response.context['variant_colors']
        sizes = response.context['variant_sizes']
        self.assertEqual(len(colors), 2)
        self.assertEqual(len(sizes), 2)
        self.assertIn('Нікель', [c['label'] for c in colors])
        nickel = next(v for v in self.variants if v.color_code == 'N' and v.size_mm == 70)
        self.assertEqual(nickel.price, Decimal('500'))
        self.assertEqual(nickel.old_price, Decimal('650'))
        self.assertEqual(nickel.stock, 3)

    def test_spec_groups(self):
        response = self.client.get(reverse('catalog:product', args=[self.product.slug]))
        groups = response.context['spec_groups']
        self.assertTrue(groups)
        self.assertEqual(groups[0]['title'], 'Загальне')

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
