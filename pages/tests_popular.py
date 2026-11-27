from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from catalog.models import Category, Product
from pages.models_cms import SiteSettings
from pages.models_popular import HomePopularProduct
from pages.popular_products import (
    READY_KEY,
    READY_PAGE,
    ensure_default_popular,
    get_home_popular,
    reset_demo_popular,
)


class HomePopularCmsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "popadmin", "pop@example.com", "pass12345"
        )
        SiteSettings.load()
        self.cat = Category.objects.create(name="Замки", slug="locks-pop")
        self.hit = Product.objects.create(
            category=self.cat,
            name="Hit Lock",
            slug="hit-lock",
            sku="HIT-1",
            price=Decimal("400"),
            old_price=Decimal("520"),
            stock=5,
            is_hit=True,
            catalog_order=1,
        )
        self.newbie = Product.objects.create(
            category=self.cat,
            name="New Lock",
            slug="new-lock",
            sku="NEW-1",
            price=Decimal("410"),
            stock=5,
            is_new=True,
            catalog_order=2,
        )
        self.other = Product.objects.create(
            category=self.cat,
            name="Other Lock",
            slug="other-lock",
            sku="OTH-1",
            price=Decimal("300"),
            stock=5,
            catalog_order=3,
        )
        HomePopularProduct.objects.all().delete()
        self.client = Client()
        self.client.force_login(self.user)

    def tearDown(self):
        translation.deactivate_all()

    def _admin(self):
        return reverse("admin:pages_homepopularsettings_change", args=[1])

    def test_admin_shows_tab_lists(self):
        ensure_default_popular()
        page = self.client.get(self._admin())
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Вкладка «Хіти»")
        self.assertContains(page, "Заголовок «Новинки»")
        self.assertContains(page, "Вкладка «Знижки»")
        self.assertContains(page, "Hit Lock")
        self.assertContains(page, "Додати товар")

    def test_seed_copies_flags_then_manual_hide(self):
        created = ensure_default_popular()
        self.assertGreaterEqual(created, 1)
        hits = get_home_popular()["hits"]
        self.assertEqual([p.sku for p in hits], ["HIT-1"])
        HomePopularProduct.objects.filter(
            tab=HomePopularProduct.Tab.HITS, product=self.hit
        ).update(is_active=False)
        self.assertEqual(get_home_popular()["hits"], [])

    def test_empty_after_ready_does_not_reseed(self):
        ensure_default_popular()
        HomePopularProduct.objects.all().delete()
        self.assertEqual(get_home_popular()["hits"], [])
        self.assertFalse(HomePopularProduct.objects.exists())

    def test_frontend_uses_curated_order(self):
        HomePopularProduct.objects.create(
            tab=HomePopularProduct.Tab.HITS,
            product=self.other,
            sort_order=1,
            is_active=True,
        )
        HomePopularProduct.objects.create(
            tab=HomePopularProduct.Tab.HITS,
            product=self.hit,
            sort_order=2,
            is_active=True,
        )
        from pages.models_cms import SiteBlock

        SiteBlock.objects.update_or_create(
            page=READY_PAGE,
            key=READY_KEY,
            defaults={"text_html": "1"},
        )
        with translation.override("ua"):
            page = self.client.get("/ua/")
        body = page.content.decode()
        hits_chunk = body[
            body.index('data-pop-panel="hits"') : body.index('data-pop-panel="sales"')
        ]
        self.assertLess(hits_chunk.index("Other Lock"), hits_chunk.index("Hit Lock"))
        self.assertNotIn("New Lock", hits_chunk)

    def test_formset_adds_and_removes(self):
        from pages.admin_popular import build_popular_formset
        from pages.models_cms import SiteBlock

        SiteBlock.objects.update_or_create(
            page=READY_PAGE,
            key=READY_KEY,
            defaults={"text_html": "1"},
        )
        HomePopularProduct.objects.create(
            tab=HomePopularProduct.Tab.HITS,
            product=self.hit,
            sort_order=0,
            is_active=True,
        )
        fs = build_popular_formset()
        data = {f"popular-{k}": v for k, v in fs.management_form.initial.items()}
        forms = fs.initial_forms
        data["popular-TOTAL_FORMS"] = str(len(forms) + 1)
        for i, form in enumerate(forms):
            inst = form.instance
            data[f"popular-{i}-id"] = str(inst.pk)
            data[f"popular-{i}-tab"] = inst.tab
            data[f"popular-{i}-product"] = str(inst.product_id)
            data[f"popular-{i}-sort_order"] = str(inst.sort_order)
            data[f"popular-{i}-is_active"] = "on"
            data[f"popular-{i}-DELETE"] = "on"
        extra = len(forms)
        data[f"popular-{extra}-tab"] = HomePopularProduct.Tab.NEWS
        data[f"popular-{extra}-product"] = str(self.other.pk)
        data[f"popular-{extra}-sort_order"] = "0"
        data[f"popular-{extra}-is_active"] = "on"
        good = build_popular_formset(data=data)
        self.assertTrue(good.is_valid(), good.errors)
        good.save()
        self.assertFalse(
            HomePopularProduct.objects.filter(
                tab=HomePopularProduct.Tab.HITS, product=self.hit
            ).exists()
        )
        self.assertTrue(
            HomePopularProduct.objects.filter(
                tab=HomePopularProduct.Tab.NEWS, product=self.other, is_active=True
            ).exists()
        )

    def test_reset_demo_reseeds_from_flags(self):
        HomePopularProduct.objects.create(
            tab=HomePopularProduct.Tab.HITS,
            product=self.other,
            sort_order=0,
            is_active=True,
        )
        reset_demo_popular()
        hits = get_home_popular()["hits"]
        self.assertEqual([p.sku for p in hits], ["HIT-1"])
        news = get_home_popular()["news"]
        self.assertEqual([p.sku for p in news], ["NEW-1"])

    def test_home_demo_clones_replaced_with_access_locks(self):
        from pages.models_cms import SiteBlock

        access = Category.objects.filter(
            name="Контроль доступу", parent__isnull=True
        ).first() or Category.objects.create(
            name="Контроль доступу", slug="access-pop"
        )
        leaf = access.children.first() or Category.objects.create(
            name="Кодові замки", slug="code-locks-pop", parent=access
        )
        code = Product.objects.create(
            category=leaf,
            name="Кодовий замок Ylli YB-300",
            slug="ylli-yb-300",
            sku="15000",
            price=Decimal("400"),
            old_price=Decimal("520"),
            stock=12,
            is_active=True,
            catalog_order=1,
        )
        HomePopularProduct.objects.all().delete()
        clone_name = (
            "Циліндр ABARO B100 60 (30*30) G латунь полірована 5 ключів"
        )
        for index in range(8):
            clone = Product.objects.create(
                category=self.cat,
                name=clone_name,
                slug=f"home-hit-{index}",
                sku=f"HOME-HIT-{index}",
                price=Decimal("400"),
                stock=12,
                is_hit=True,
                is_active=True,
                catalog_order=index,
            )
            HomePopularProduct.objects.create(
                tab=HomePopularProduct.Tab.HITS,
                product=clone,
                sort_order=index,
                is_active=True,
            )
        SiteBlock.objects.update_or_create(
            page=READY_PAGE,
            key=READY_KEY,
            defaults={"text_html": "1"},
        )
        hits = get_home_popular()["hits"]
        skus = [product.sku for product in hits]
        self.assertNotIn("HOME-HIT-0", skus)
        self.assertIn(code.sku, skus)
        self.assertTrue(any("Ylli" in product.name for product in hits))
        self.assertEqual(len({product.name for product in hits}), len(hits))
