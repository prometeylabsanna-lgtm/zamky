from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from catalog.admin_parent_cascade import build_parent_cascade_tree
from catalog.category_tree import (
    category_path_label,
    ensure_category_tree,
    menu_payload,
    resolve_leaf_category,
    subtree_ids,
)
from catalog.menu_align import reassign_products_to_menu
from catalog.models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
)


class CategoryTreeTests(TestCase):
    def setUp(self):
        ensure_category_tree()
        self.root = Category.objects.get(
            name='Циліндри', parent__isnull=True, is_active=True
        )

    def test_menu_payload_from_db(self):
        payload = menu_payload()
        names = [row['name'] for row in payload]
        self.assertIn('Циліндри', names)
        self.assertIn('Замки', names)
        self.assertNotIn('Серцевини (циліндри)', names)
        self.assertNotIn('Guardian', names)
        cyl = next(row for row in payload if row['name'] == 'Циліндри')
        self.assertEqual(cyl['lock'], 'cyl')
        self.assertTrue(cyl['url'])
        sub_names = [s['name'] for s in cyl['subs']]
        self.assertEqual(len(sub_names), len(set(sub_names)))
        self.assertIn('Ключ-ключ', sub_names)
        kk = next(s for s in cyl['subs'] if s['name'] == 'Ключ-ключ')
        leaf_names = [leaf['name'] for leaf in kk['leaves']]
        self.assertEqual(leaf_names, ['Стандартні', 'Підвищеної секретності'])
        self.assertTrue(kk['leaves'][0]['url'])

    def test_renames_old_cylinder_root(self):
        Product.objects.all().delete()
        Category.objects.all().delete()
        old = Category.objects.create(
            name='Серцевини (циліндри)', slug='old-cyl', icon='cyl'
        )
        ensure_category_tree()
        old.refresh_from_db()
        self.assertEqual(old.name, 'Циліндри')
        names = [row['name'] for row in menu_payload()]
        self.assertIn('Циліндри', names)
        self.assertNotIn('Серцевини (циліндри)', names)

    def test_nested_cylinder_alias_moves_products(self):
        Product.objects.all().delete()
        Category.objects.all().delete()
        locks = Category.objects.create(name='Замки', slug='locks-n')
        nested = Category.objects.create(
            name='Серцевини (циліндри)', slug='nested-cyl', parent=locks
        )
        kk = Category.objects.create(
            name='Ключ / ключ', slug='kk-old', parent=nested
        )
        product = Product.objects.create(
            category=kk,
            name='Циліндр Test',
            slug='cyl-t',
            sku='ABR-T',
            price=Decimal('10'),
            catalog_order=1,
        )
        ensure_category_tree()
        reassign_products_to_menu()
        product.refresh_from_db()
        path = category_path_label(product.category)
        self.assertIn('Циліндри', path)
        self.assertNotIn('Врізні замки', path)

    def test_subtree_includes_leaves(self):
        leaf = Category.objects.get(name='Стандартні', parent__name='Ключ-ключ')
        ids = subtree_ids(self.root.pk)
        self.assertIn(leaf.pk, ids)
        self.assertIn(self.root.pk, ids)

    def test_resolve_leaf_by_mech_and_size(self):
        leaf = resolve_leaf_category(self.root, 'Ключ / ключ', '30×30')
        self.assertIsNotNone(leaf)
        self.assertEqual(leaf.name, 'Стандартні')
        half = resolve_leaf_category(self.root, 'Половинчастий', '10×30')
        self.assertIsNotNone(half)
        self.assertEqual(half.name, 'Половинчасті циліндри')

    def test_catalog_leaf_vs_root(self):
        kk = Category.objects.get(name='Ключ-ключ', parent=self.root)
        leaf = Category.objects.get(name='Стандартні', parent=kk)
        other = Category.objects.get(name='Підвищеної секретності', parent=kk)
        p_leaf = Product.objects.create(
            category=leaf,
            name='Leaf p',
            slug='leaf-p',
            sku='LEAF-1',
            price=Decimal('10'),
            catalog_order=1,
        )
        Product.objects.create(
            category=other,
            name='Other p',
            slug='other-p',
            sku='LEAF-2',
            price=Decimal('10'),
            catalog_order=1,
        )
        root_page = self.client.get(
            reverse('catalog:category', args=[self.root.slug]), follow=True
        )
        skus = [p.sku for p in root_page.context['products']]
        self.assertIn(p_leaf.sku, skus)
        self.assertIn('LEAF-2', skus)
        leaf_page = self.client.get(
            reverse('catalog:category', args=[leaf.slug]), follow=True
        )
        leaf_skus = [p.sku for p in leaf_page.context['products']]
        self.assertIn('LEAF-1', leaf_skus)
        self.assertNotIn('LEAF-2', leaf_skus)


class DynamicFilterTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Тест', slug='dyn-cat')
        attr = Attribute.objects.create(
            name='Країна', slug='country', filterable=True, sort_order=1
        )
        hidden = Attribute.objects.create(
            name='Секрет', slug='secret-f', filterable=True, sort_order=2
        )
        self.av = AttributeValue.objects.create(
            attribute=attr, value='Туреччина', slug='turkey'
        )
        AttributeValue.objects.create(
            attribute=hidden, value='Нічого', slug='none-val'
        )
        p = Product.objects.create(
            category=self.cat,
            name='P',
            slug='dyn-p',
            sku='DYN-1',
            price=Decimal('50'),
            catalog_order=1,
        )
        ProductAttribute.objects.create(product=p, attribute_value=self.av)

    def test_filterable_slug_not_hardcoded(self):
        page = self.client.get(
            reverse('catalog:catalog'), {'country': 'turkey'}, follow=True
        )
        products = list(page.context['products'])
        self.assertEqual([p.sku for p in products], ['DYN-1'])
        titles = [g['title'] for g in page.context['filter_groups']]
        self.assertIn('Країна', titles)
        self.assertNotIn('Секрет', titles)


class CategoryAdminNavTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            'cadmin', 'c@example.com', 'pass12345'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.root = Category.objects.create(
            name='Корінь', slug='root-nav', icon='cyl'
        )
        self.child = Category.objects.create(
            name='Дитина', slug='child-nav', parent=self.root
        )

    def test_drill_down(self):
        hub = reverse('admin:catalog_category_changelist')
        roots = self.client.get(hub)
        self.assertEqual(roots.status_code, 200)
        self.assertContains(roots, 'Корінь')
        self.assertContains(roots, 'Додати категорію')
        self.assertContains(roots, 'filter-nav__thumb')
        self.assertContains(roots, 'M8.4 9.6A4 4 0 1 1 15.6 9.6')
        change = reverse('admin:catalog_category_change', args=[self.root.pk])
        self.assertContains(roots, f'class="filter-nav__thumb" href="{change}')
        kids = self.client.get(hub, {'parent': self.root.pk})
        self.assertContains(kids, 'Дитина')
        self.assertContains(kids, 'Корінь')

    def test_parent_cascade_tree_skips_self(self):
        tree = build_parent_cascade_tree(exclude_pk=self.root.pk)
        ids = [row['id'] for row in tree]
        self.assertNotIn(self.root.pk, ids)
        self.assertNotIn(self.child.pk, ids)

    def test_parent_cascade_on_form(self):
        url = reverse('admin:catalog_category_change', args=[self.root.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'data-parent-cascade')
        self.assertContains(page, 'data-cascade-toggle')
        self.assertContains(page, 'data-cascade-col="1"')
        self.assertContains(page, 'data-cascade-col="3"')
        self.assertNotContains(
            page, 'Серцевини (циліндри) / Ключ / ключ / 30×30 мм'
        )

    def test_occupied_category_not_deletable(self):
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory

        from catalog.admin import CategoryAdmin

        Product.objects.create(
            category=self.root,
            name='Зайнятий',
            slug='occupied-nav',
            sku='OCC-NAV-1',
            price=Decimal('10'),
            catalog_order=1,
        )
        req = RequestFactory().get('/')
        req.user = self.user
        admin = CategoryAdmin(Category, AdminSite())
        self.assertFalse(admin.has_delete_permission(req, self.root))
        self.assertTrue(admin.has_delete_permission(req, self.child))
