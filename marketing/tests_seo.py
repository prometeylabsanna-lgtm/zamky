from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase

from catalog.models import Category, Product
from marketing.models import SeoSettings
from orders.models import DeliveryDistrict
from pages.models_extra import BlogPost


class SeoIndexFilesTests(TestCase):
    def setUp(self):
        cache.clear()
        seo = SeoSettings.load()
        seo.primary_domain = "https://zamky.example"
        seo.save()
        self.cat = Category.objects.create(name="Циліндри", slug="cyl-seo")
        self.product = Product.objects.create(
            category=self.cat,
            name="Замок SEO",
            slug="zamok-seo",
            sku="SEO-1",
            price=Decimal("100.00"),
            stock=3,
            is_active=True,
            short_description="Короткий опис замка для дверей у Києві з доставкою.",
        )
        BlogPost.objects.create(
            title="Як вибрати замок",
            slug="yak-vybraty-seo",
            excerpt="Поради з вибору замка для вхідних дверей.",
            body="<p>Текст</p>",
            is_published=True,
        )

    def test_root_permanent_redirect(self):
        resp = self.client.get("/", follow=False)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp["Location"], "/ua/")

    def test_sitemap_has_indexable_urls_only(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("https://zamky.example/ua/", body)
        self.assertIn("https://zamky.example/ru/", body)
        self.assertIn("/ua/catalog/", body)
        self.assertIn("/ua/product/zamok-seo/", body)
        self.assertIn("/ua/catalog/cyl-seo/", body)
        self.assertIn("/ua/info/about/", body)
        self.assertIn("/ua/info/blog/", body)
        self.assertIn("/ua/info/blog/yak-vybraty-seo/", body)
        self.assertIn('hreflang="uk"', body)
        self.assertIn('hreflang="x-default"', body)
        self.assertNotIn("/kyiv/", body)
        self.assertNotIn("/checkout/", body)
        self.assertNotIn("/cart/", body)
        self.assertNotIn("/order/", body)
        self.assertNotIn("?sort=", body)

    def test_robots_disallows_and_sitemap(self):
        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("User-agent: *", body)
        self.assertIn("Disallow: /admin/", body)
        self.assertIn("Disallow: /feeds/", body)
        self.assertIn("Disallow: /healthz/", body)
        self.assertIn("Disallow: /lang/", body)
        self.assertIn("Disallow: /ua/cart/", body)
        self.assertIn("Disallow: /ru/checkout/", body)
        self.assertIn("Disallow: /ua/order/", body)
        self.assertIn("Disallow: /ua/api/", body)
        self.assertIn("Disallow: /ua/install/", body)
        self.assertNotIn("Disallow: /ua/info/install/", body)
        self.assertIn("Sitemap: https://zamky.example/sitemap.xml", body)
        self.assertNotIn("Disallow: /static/", body)
        self.assertNotIn("Disallow: /media/", body)

    def test_llms_txt_from_real_pages(self):
        body = self.client.get("/llms.txt").content.decode()
        self.assertIn("Циліндри", body)
        self.assertIn("/ua/catalog/cyl-seo/", body)
        self.assertIn("Як вибрати замок", body)
        self.assertIn("/ua/info/about/", body)
        self.assertNotIn("Lorem ipsum", body)
        self.assertNotIn("info@centrzamkiv.ua", body)


class SeoNoindexCanonicalTests(TestCase):
    def setUp(self):
        cache.clear()
        seo = SeoSettings.load()
        seo.primary_domain = "https://zamky.example"
        seo.save()
        DeliveryDistrict.objects.create(
            slug="obolon",
            name="Оболонський",
            short="Оболонь",
            is_active=True,
        )
        Category.objects.create(name="Каталог", slug="cat-seo")

    def _head(self, url):
        html = self.client.get(url).content.decode()
        return html.split("</head>")[0]

    def test_checkout_noindex_follow(self):
        head = self._head("/ua/checkout/")
        self.assertIn('name="robots" content="noindex, follow"', head)

    def test_wishlist_noindex(self):
        head = self._head("/ua/cart/wishlist/")
        self.assertIn("noindex", head)
        self.assertNotIn("nofollow", head.split("noindex")[1][:40])

    def test_district_noindex_without_canonical(self):
        head = self._head("/ua/kyiv/obolon/")
        self.assertIn("noindex", head)
        self.assertNotIn('rel="canonical"', head)
        self.assertNotIn('hreflang="uk"', head)

    def test_city_noindex(self):
        head = self._head("/ua/kyiv/")
        self.assertIn("noindex", head)
        self.assertNotIn('rel="canonical"', head)

    def test_search_noindex_without_canonical_to_listing(self):
        head = self._head("/ua/catalog/?q=замок")
        self.assertIn("noindex", head)
        self.assertNotIn('rel="canonical"', head)

    def test_facet_noindex_canonical_to_clean_path(self):
        head = self._head("/ua/catalog/?sort=cheap")
        self.assertIn("noindex", head)
        self.assertIn('rel="canonical" href="https://zamky.example/ua/catalog/"', head)

    def test_home_indexable_with_hreflang(self):
        head = self._head("/ua/")
        self.assertNotIn("noindex", head)
        self.assertIn('rel="canonical" href="https://zamky.example/ua/"', head)
        self.assertIn('hreflang="ru"', head)
        self.assertIn("https://zamky.example/ru/", head)

    def test_global_noindex_is_nofollow(self):
        seo = SeoSettings.load()
        seo.global_noindex = True
        seo.save()
        head = self._head("/ua/")
        self.assertIn('content="noindex, nofollow"', head)


class SeoProductSignalsTests(TestCase):
    def setUp(self):
        cache.clear()
        seo = SeoSettings.load()
        seo.primary_domain = "https://zamky.example"
        seo.save()
        self.cat = Category.objects.create(name="Циліндри", slug="cyl-pdp")
        self.product = Product.objects.create(
            category=self.cat,
            name="Замок PDP",
            slug="zamok-pdp",
            sku="PDP-1",
            price=Decimal("250.50"),
            stock=2,
            is_active=True,
            brand="ABARO",
            short_description="Циліндр для вхідних дверей з гарантією виробника.",
        )

    def test_product_jsonld_and_short_description(self):
        html = self.client.get("/ua/product/zamok-pdp/").content.decode()
        self.assertIn('"@type":"Product"', html)
        self.assertIn('"sku":"PDP-1"', html)
        self.assertIn("250.50", html)
        self.assertNotIn("AggregateRating", html)
        self.assertIn("Циліндр для вхідних дверей", html.split("</head>")[0])
        self.assertIn('property="og:type" content="product"', html)

    def test_product_uses_own_seo_description(self):
        self.product.seo_description = "Унікальний SEO опис товару для видачі Google Київ."
        self.product.save(update_fields=["seo_description"])
        head = self.client.get("/ua/product/zamok-pdp/").content.decode().split("</head>")[0]
        self.assertIn("Унікальний SEO опис товару", head)
