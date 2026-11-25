from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from catalog.models import Attribute, AttributeValue, Category, Product
from pages.models_cms import SiteSettings
from pages.models_picker import PickerDoor, PickerFilter, PickerFilterOption
from pages.picker_defaults import ensure_picker_defaults, get_picker_options_json
from pages.site_content_registry import build_content_sidebar_groups, get_section


class HomePickerCmsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            "pickadmin", "pick@example.com", "pass12345"
        )
        SiteSettings.load()
        ensure_picker_defaults()
        self.client = Client()
        self.client.force_login(self.user)

    def tearDown(self):
        translation.deactivate_all()

    def _texts(self):
        return reverse("admin:pages_homepickersettings_change", args=[1])

    def _doors(self, extra=""):
        url = reverse("admin:pages_homepickerdoorssettings_change", args=[1])
        if extra:
            url = f"{url}?{extra.lstrip('?')}"
        return url

    def _filters(self, extra=""):
        url = reverse("admin:pages_homepickerfilterssettings_change", args=[1])
        if extra:
            url = f"{url}?{extra.lstrip('?')}"
        return url

    def _style(self):
        return reverse("admin:pages_homepickerstylesettings_change", args=[1])

    def test_sidebar_has_picker_subsections(self):
        groups = build_content_sidebar_groups(admin_prefix="admin/")
        group_titles = [g["title"] for g in groups]
        self.assertEqual(group_titles[:3], ["Оболонка сайту", "Головна", "Підбір"])
        picker = next(g for g in groups if g["title"] == "Підбір")
        titles = [item["title"] for item in picker["items"]]
        self.assertEqual(titles, ["Тексти", "Двері", "Фільтри", "Оформлення"])
        home = next(g for g in groups if g["title"] == "Головна")
        home_titles = [item["title"] for item in home["items"]]
        self.assertNotIn("Підбір", home_titles)
        self.assertNotIn("Шапка", home_titles)

    def test_texts_page_has_ua_ru_not_doors(self):
        page = self.client.get(self._texts())
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Швидкий підбір замка")
        self.assertContains(page, "data-admin-lang")
        self.assertNotContains(page, "data-admin-panel-label=\"Двері\"")
        self.assertIsNotNone(get_section("home", "picker"))
        self.assertFalse(get_section("home", "picker").include_style)

    def test_doors_page_has_ru_fields(self):
        page = self.client.get(self._doors())
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Вхідні двері")
        self.assertContains(page, "Рядок 1 (RU)")
        self.assertContains(page, "label_line1_ru")
        self.assertContains(page, "data-admin-lang=\"ru\"")
        self.assertContains(page, "Категорії товарів")
        self.assertNotContains(page, "data-admin-panel-label=\"Фільтри\"")

    def test_filters_page_has_options_and_ru(self):
        page = self.client.get(self._filters("filter=price"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Варіанти вибору")
        self.assertContains(page, "до 1500")
        self.assertContains(page, "Новий варіант")
        self.assertContains(page, "Видалити")
        self.assertContains(page, "Додати")
        self.assertContains(page, "Варіант (RU)")
        self.assertContains(page, "label_ru")

    def test_style_page(self):
        page = self.client.get(self._style())
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Колір фону")
        self.assertNotContains(page, "data-admin-lang-tab")

    def test_add_door_shows_on_home(self):
        response = self.client.post(
            self._doors("new=1"),
            {
                "door_new": "1",
                "label_line1": "Скляні",
                "label_line1_ru": "Стеклянные",
                "label_line2": "двері",
                "label_line2_ru": "двери",
                "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        created = PickerDoor.objects.get(label_line1="Скляні")
        last = PickerDoor.objects.order_by("sort_order").last()
        self.assertEqual(created.pk, last.pk)
        self.assertEqual(created.label_line1_ru, "Стеклянные")
        home = self.client.get("/ua/")
        self.assertContains(home, "Скляні")
        home_ru = self.client.get("/ru/")
        self.assertContains(home_ru, "Стеклянные")

    def test_add_and_delete_filter_option(self):
        filt = PickerFilter.objects.get(key="price")
        initial = filt.options.count()
        existing = list(filt.options.order_by("sort_order", "pk"))
        payload = {
            "label": filt.label,
            "label_ru": filt.label_ru,
            "is_active": "on",
            "options-TOTAL_FORMS": str(initial + 1),
            "options-INITIAL_FORMS": str(initial),
            "options-MIN_NUM_FORMS": "0",
            "options-MAX_NUM_FORMS": "1000",
        }
        for i, opt in enumerate(existing):
            payload[f"options-{i}-id"] = str(opt.pk)
            payload[f"options-{i}-label"] = opt.label
            payload[f"options-{i}-label_ru"] = opt.label_ru
            payload[f"options-{i}-value"] = opt.value
            if opt.price_min is not None:
                payload[f"options-{i}-price_min"] = str(opt.price_min)
            if opt.price_max is not None:
                payload[f"options-{i}-price_max"] = str(opt.price_max)
        payload[f"options-{initial}-label"] = "до 800 ₴"
        payload[f"options-{initial}-label_ru"] = "до 800 ₴"
        payload[f"options-{initial}-value"] = ""
        payload[f"options-{initial}-price_min"] = "0"
        payload[f"options-{initial}-price_max"] = "800"
        response = self.client.post(
            self._filters("filter=price"),
            payload,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            PickerFilterOption.objects.filter(filter=filt, label="до 800 ₴").exists()
        )
        labels = [row["label"] for row in get_picker_options_json()["price"]]
        self.assertIn("до 800 ₴", labels)

        created = PickerFilterOption.objects.get(filter=filt, label="до 800 ₴")
        payload["options-TOTAL_FORMS"] = str(initial + 1)
        payload["options-INITIAL_FORMS"] = str(initial + 1)
        payload[f"options-{initial}-id"] = str(created.pk)
        payload[f"options-{initial}-label"] = created.label
        payload[f"options-{initial}-value"] = created.value
        payload[f"options-{initial}-DELETE"] = "on"
        response = self.client.post(
            self._filters("filter=price"),
            payload,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            PickerFilterOption.objects.filter(pk=created.pk).exists()
        )

    def test_add_and_delete_filter(self):
        country = Attribute.objects.create(
            name="Країна виробництва", slug="country", filterable=True
        )
        AttributeValue.objects.create(
            attribute=country, value="Італія", slug="italy", sort_order=0
        )
        blank = self.client.get(self._filters("new=1"))
        self.assertEqual(blank.status_code, 200)
        self.assertContains(blank, "Оберіть фільтр каталогу")
        response = self.client.post(
            self._filters("new=1"),
            {
                "filter_new": "1",
                "attribute": str(country.pk),
                "label": "Country",
                "label_ru": "Страна",
                "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        created = PickerFilter.objects.get(key="country")
        self.assertEqual(created.label, "Country")
        self.assertEqual(created.label_ru, "Страна")
        self.assertEqual(created.attribute_id, country.pk)
        self.assertTrue(
            PickerFilterOption.objects.filter(
                filter=created, value="italy"
            ).exists()
        )
        last = PickerFilter.objects.order_by("sort_order").last()
        self.assertEqual(created.pk, last.pk)
        home = self.client.get("/ua/")
        self.assertContains(home, "Country")
        self.assertContains(home, 'data-filter="country"')
        home_ru = self.client.get("/ru/")
        self.assertContains(home_ru, "Страна")

        response = self.client.post(
            self._filters("filter=country"),
            {
                "filter_new": "0",
                "delete_filter": "1",
                "label": created.label,
                "label_ru": created.label_ru,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PickerFilter.objects.filter(pk=created.pk).exists())
        home = self.client.get("/ua/")
        self.assertNotContains(home, 'data-filter="country"')

    def test_door_categories_filter_products(self):
        locks = Category.objects.create(name="Замки", slug="locks")
        cyl = Category.objects.create(name="Серцевини", slug="cyl")
        lock = Product.objects.create(
            category=locks,
            name="Lock",
            slug="lock-1",
            sku="L-1",
            price=Decimal("100"),
            stock=3,
            catalog_order=1,
        )
        Product.objects.create(
            category=cyl,
            name="Cyl",
            slug="cyl-1",
            sku="C-1",
            price=Decimal("200"),
            stock=3,
            catalog_order=2,
        )
        door = PickerDoor.objects.get(code="0")
        door.categories.set([locks])
        with translation.override("ua"):
            data = self.client.get(
                reverse("catalog:api_picker"), {"door": "0"}
            ).json()
        slugs = {item["slug"] for item in data["items"]}
        self.assertIn(lock.slug, slugs)
        self.assertNotIn("cyl-1", slugs)
        self.assertFalse(data.get("fallback"))

    def test_picker_fallback_popular(self):
        cat = Category.objects.create(name="Замки", slug="locks-fb")
        hit = Product.objects.create(
            category=cat,
            name="Hit",
            slug="hit-1",
            sku="H-1",
            price=Decimal("100"),
            stock=2,
            catalog_order=1,
            is_hit=True,
        )
        attr = Attribute.objects.create(name="Країна", slug="country-fb")
        filt = PickerFilter.objects.create(
            key="country-fb",
            label="Країна",
            attribute=attr,
            sort_order=9,
            is_active=True,
        )
        PickerFilterOption.objects.create(
            filter=filt, label="X", value="no-such", sort_order=0, is_active=True
        )
        with translation.override("ua"):
            response = self.client.get(
                reverse("catalog:api_picker"), {"country-fb": "no-such"}
            )
        self.assertEqual(response.status_code, 200, response.content[:1500])
        data = response.json()
        self.assertTrue(data["fallback"])
        self.assertTrue(data["items"])
        self.assertEqual(data["items"][0]["slug"], hit.slug)
