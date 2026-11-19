import shutil
import tempfile
from decimal import Decimal

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from lxml import etree

from catalog.models import Category, Product, ProductImage
from marketing.feeds import G_NS, collect_items, format_price, get_feed_payload
from marketing.models import ProductFeed, SeoSettings, TrackingSettings
from pages.models_cms import SiteSettings

GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00"
    b"\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)
MEDIA = tempfile.mkdtemp(prefix="zamky-mkt-test-")
G = "{%s}" % G_NS


def _img(name="p.gif"):
    return SimpleUploadedFile(name, GIF, content_type="image/gif")


@override_settings(MEDIA_ROOT=MEDIA)
class FeedTestBase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()
        seo = SeoSettings.load()
        seo.primary_domain = "https://zamky.example"
        seo.save()
        self.root = Category.objects.create(name="Замки", slug="locks")
        self.child = Category.objects.create(name="Циліндри", slug="cyl", parent=self.root)
        self.other = Category.objects.create(name="Інше", slug="other")
        self.p1 = self._product("SKU-1", "Замок A&B «Pro»", Decimal("1234.5"), cat=self.child, stock=5, brand="ABARO")
        self.feed = ProductFeed.objects.create(
            name="G", feed_type="google", slug="g-test", is_enabled=True, shop_name="Центр замків"
        )

    def _product(self, sku, name, price, cat=None, stock=1, old_price=None, image=True, brand="", slug=None):
        p = Product.objects.create(
            category=cat or self.root, name=name, slug=slug or sku.lower(), sku=sku, price=price,
            old_price=old_price, stock=stock, brand=brand,
            description="<p>Опис &amp; <b>деталі</b></p>",
        )
        if image:
            ProductImage.objects.create(product=p, image=_img(f"{sku}.gif"))
        return p

    def _xml(self, feed=None):
        payload = get_feed_payload(feed or self.feed, "https://zamky.example", force=True)
        return etree.fromstring(payload.body), payload


class GoogleFeedTests(FeedTestBase):
    def test_valid_rss_with_escaping_and_fields(self):
        root, payload = self._xml()
        self.assertEqual(root.tag, "rss")
        item = root.find("channel/item")
        self.assertEqual(item.findtext(G + "id"), "SKU-1")
        self.assertEqual(item.findtext(G + "title"), "Замок A&B «Pro»")
        self.assertIn(b"A&amp;B", payload.body)
        self.assertEqual(item.findtext(G + "description"), "Опис & деталі")
        self.assertEqual(item.findtext(G + "price"), "1234.50 UAH")
        self.assertEqual(item.findtext(G + "availability"), "in_stock")
        self.assertEqual(item.findtext(G + "condition"), "new")
        self.assertEqual(item.findtext(G + "brand"), "ABARO")
        self.assertTrue(item.findtext(G + "link").startswith("https://zamky.example/ua/product/"))
        self.assertTrue(item.findtext(G + "image_link").startswith("https://zamky.example/"))
        self.assertEqual(item.findtext(G + "product_type"), "Замки > Циліндри")
        self.assertIsNone(item.find(G + "gtin"))
        self.assertEqual(item.findtext(G + "identifier_exists"), "no")
        self.assertIsNone(item.find(G + "shipping"))

    def test_title_strips_html(self):
        self.p1.name = "Замок <b>A&amp;B</b> <script>x</script>"
        self.p1.save()
        root, payload = self._xml()
        self.assertEqual(root.find("channel/item").findtext(G + "title"), "Замок A&B x")
        self.assertNotIn(b"<b>", payload.body)
        self.assertNotIn(b"<script>", payload.body)
        self.assertNotIn(b"&lt;b&gt;", payload.body)

    def test_sale_price_when_old_price_higher(self):
        self.p1.old_price = Decimal("1500")
        self.p1.save()
        root, _ = self._xml()
        item = root.find("channel/item")
        self.assertEqual(item.findtext(G + "price"), "1500.00 UAH")
        self.assertEqual(item.findtext(G + "sale_price"), "1234.50 UAH")

    def test_currency_from_feed(self):
        self.feed.currency = "EUR"
        self.feed.save()
        root, _ = self._xml()
        self.assertTrue(root.find("channel/item").findtext(G + "price").endswith(" EUR"))
        self.assertEqual(format_price(Decimal("5"), "UAH"), "5.00 UAH")

    def test_exclusions_counted(self):
        self._product("SKU-0", "Zero", Decimal("0"))
        self._product("SKU-NOIMG", "NoImg", Decimal("10"), image=False)
        inactive = Category.objects.create(name="Off", slug="off", is_active=False)
        self._product("SKU-OFF", "Off", Decimal("10"), cat=inactive)
        hidden = self._product("SKU-HID", "Hidden", Decimal("10"))
        hidden.is_active = False
        hidden.save()
        result = collect_items(self.feed, "https://zamky.example")
        self.assertEqual([i.id for i in result.items], ["SKU-1"])
        self.assertEqual(result.reasons, {"price_not_positive": 1, "no_image": 1, "inactive_category": 1})
        get_feed_payload(self.feed, "https://zamky.example", force=True)
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.last_excluded, 3)

    def test_category_filter_includes_children_and_stock_filter(self):
        self._product("SKU-OTHER", "Other", Decimal("10"), cat=self.other)
        self._product("SKU-OUT", "Out", Decimal("10"), cat=self.root, stock=0)
        self.feed.categories.set([self.root])
        ids = [i.id for i in collect_items(self.feed, "https://zamky.example").items]
        self.assertEqual(sorted(ids), ["SKU-1", "SKU-OUT"])
        self.feed.only_in_stock = True
        self.feed.save()
        ids = [i.id for i in collect_items(self.feed, "https://zamky.example").items]
        self.assertEqual(ids, ["SKU-1"])

    def test_out_of_stock_availability(self):
        self.p1.stock = 0
        self.p1.save()
        root, _ = self._xml()
        self.assertEqual(root.find("channel/item").findtext(G + "availability"), "out_of_stock")

    def test_google_category_mapping_from_ancestor(self):
        self.feed.category_mappings.create(category=self.root, google_product_category=2678)
        root, _ = self._xml()
        self.assertEqual(root.find("channel/item").findtext(G + "google_product_category"), "2678")

    def test_http_view_headers_404_token_and_etag(self):
        r = self.client.get("/feeds/g-test.xml")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/xml; charset=utf-8")
        self.assertTrue(r["ETag"])
        self.assertTrue(r["Last-Modified"])
        r304 = self.client.get("/feeds/g-test.xml", HTTP_IF_NONE_MATCH=r["ETag"])
        self.assertEqual(r304.status_code, 304)
        self.feed.access_token = "s3cret-token"
        self.feed.save()
        self.assertEqual(self.client.get("/feeds/g-test.xml").status_code, 404)
        self.assertEqual(self.client.get("/feeds/g-test.xml?token=bad").status_code, 404)
        self.assertEqual(self.client.get("/feeds/g-test.xml?token=s3cret-token").status_code, 200)
        self.feed.is_enabled = False
        self.feed.save()
        self.assertEqual(self.client.get("/feeds/g-test.xml?token=s3cret-token").status_code, 404)

    def test_cache_invalidated_on_product_save(self):
        first = get_feed_payload(self.feed, "https://zamky.example")
        self.p1.name = "Новий замок"
        self.p1.save()
        second = get_feed_payload(self.feed, "https://zamky.example")
        self.assertNotEqual(first.etag, second.etag)
        self.assertIn("Новий замок".encode(), second.body)

    def test_no_internal_fields(self):
        _, payload = self._xml()
        for word in (b"purchase", b"supplier", b"stock>"):
            self.assertNotIn(word, payload.body)


class PromFeedTests(FeedTestBase):
    def test_yml_structure_and_cdata(self):
        feed = ProductFeed.objects.create(
            name="P", feed_type="prom", slug="p-test", is_enabled=True, shop_name="Центр замків", company_name="ТОВ Замки"
        )
        _, payload = self._xml(feed)
        self.assertIn(b"<![CDATA[", payload.body)
        root = etree.fromstring(payload.body)
        self.assertEqual(root.tag, "yml_catalog")
        self.assertTrue(root.get("date"))
        self.assertEqual(root.findtext("shop/company"), "ТОВ Замки")
        self.assertEqual(root.find("shop/currencies/currency").get("id"), "UAH")
        cats = {c.get("id"): c.get("parentId") for c in root.findall("shop/categories/category")}
        self.assertEqual(cats[str(self.child.pk)], str(self.root.pk))
        offer = root.find("shop/offers/offer")
        self.assertEqual(offer.get("id"), "SKU-1")
        self.assertEqual(offer.get("available"), "true")
        self.assertEqual(offer.findtext("price"), "1234.50")
        self.assertEqual(offer.findtext("currencyId"), "UAH")
        self.assertEqual(offer.findtext("vendor"), "ABARO")
        self.assertEqual(offer.findtext("vendorCode"), "SKU-1")
        self.assertEqual(offer.findtext("quantity_in_stock"), "5")
        self.assertIsNone(offer.find("price_old"))
        self.assertIsNone(offer.find("discount"))

    def test_price_old_only_when_on_sale_and_in_stock(self):
        self.p1.old_price = Decimal("1500")
        self.p1.save()
        feed = ProductFeed.objects.create(
            name="P", feed_type="prom", slug="p-price-old", is_enabled=True, shop_name="Центр замків"
        )
        root, payload = self._xml(feed)
        offer = root.find("shop/offers/offer")
        self.assertEqual(offer.get("available"), "true")
        self.assertEqual(offer.findtext("price"), "1234.50")
        self.assertEqual(offer.findtext("price_old"), "1500.00")
        self.assertIsNone(offer.find("discount"))
        self.assertNotIn(b"<discount", payload.body)

    def test_no_price_old_when_out_of_stock(self):
        self.p1.old_price = Decimal("1500")
        self.p1.stock = 0
        self.p1.save()
        feed = ProductFeed.objects.create(
            name="P", feed_type="prom", slug="p-oos", is_enabled=True, shop_name="Центр замків"
        )
        root, _ = self._xml(feed)
        offer = root.find("shop/offers/offer")
        self.assertEqual(offer.get("available"), "false")
        self.assertEqual(offer.findtext("price"), "1234.50")
        self.assertIsNone(offer.find("price_old"))
        self.assertIsNone(offer.find("discount"))

    def test_vendorcode_omitted_when_sku_invalid(self):
        long_sku = "SKU-" + "X" * 22  # 26 символів, у Prom ліміт 25
        bad_chars = "SKU@HASH"
        self._product(long_sku, "Довгий артикул", Decimal("10"), brand="ABARO", slug="sku-too-long")
        self._product(bad_chars, "Заборонені символи", Decimal("10"), brand="ABARO", slug="sku-bad-chars")
        self._product("ОК-Артикул_1/2.", "Валідний артикул", Decimal("10"), brand="ABARO", slug="sku-ok-ua")
        feed = ProductFeed.objects.create(
            name="P", feed_type="prom", slug="p-vendor", is_enabled=True, shop_name="Центр замків"
        )
        root, payload = self._xml(feed)
        offers = {o.get("id"): o for o in root.findall("shop/offers/offer")}
        self.assertIn(long_sku, offers)
        self.assertIn(bad_chars, offers)
        self.assertIsNone(offers[long_sku].find("vendorCode"))
        self.assertIsNone(offers[bad_chars].find("vendorCode"))
        self.assertEqual(offers["SKU-1"].findtext("vendorCode"), "SKU-1")
        self.assertEqual(offers["ОК-Артикул_1/2."].findtext("vendorCode"), "ОК-Артикул_1/2.")
        feed.refresh_from_db()
        self.assertEqual(feed.last_warnings, {"vendorcode_invalid": 2})
        self.assertEqual(payload.warnings, {"vendorcode_invalid": 2})

    def test_prom_vendorcode_warning_visible_in_admin(self):
        from django.contrib.auth import get_user_model

        self._product("SKU#" + "Y" * 24, "Поганий артикул", Decimal("10"), slug="sku-hash-long")
        feed = ProductFeed.objects.create(
            name="P", feed_type="prom", slug="p-admin-warn", is_enabled=True, shop_name="Центр замків"
        )
        self._xml(feed)
        user = get_user_model().objects.create_superuser("cms", "cms@example.com", "pass")
        self.client.force_login(user)
        html = self.client.get(f"/admin/marketing/productfeed/{feed.pk}/change/", follow=True).content.decode()
        self.assertIn("vendorCode пропущено", html)
        list_html = self.client.get("/admin/marketing/productfeed/", follow=True).content.decode()
        self.assertIn(">1<", list_html)

    def test_seeded_feeds_disabled(self):
        from marketing.seed import seed_marketing

        seed_marketing(SeoSettings, TrackingSettings, ProductFeed, SiteSettings)
        prom = ProductFeed.objects.filter(feed_type="prom").exclude(slug="p-test")
        self.assertTrue(prom.exists())
        self.assertFalse(ProductFeed.objects.filter(feed_type="prom", is_enabled=True).exists())
        before = ProductFeed.objects.count()
        seed_marketing(SeoSettings, TrackingSettings, ProductFeed, SiteSettings)
        self.assertEqual(ProductFeed.objects.count(), before)


class TrackingTests(TestCase):
    def setUp(self):
        cache.clear()

    def _home(self):
        return self.client.get("/ua/").content.decode()

    def test_nothing_by_default(self):
        html = self._home()
        for marker in ("googletagmanager", "fbq(", "ttq.load", "gtag("):
            self.assertNotIn(marker, html)

    def test_enabled_requires_id(self):
        t = TrackingSettings.load()
        t.ga4_enabled = True
        with self.assertRaises(ValidationError):
            t.full_clean()

    def test_invalid_id_rejected(self):
        t = TrackingSettings.load()
        t.ga4_id = "G-1');alert(1)//"
        with self.assertRaises(ValidationError):
            t.full_clean()

    def test_output_only_when_enabled(self):
        t = TrackingSettings.load()
        t.ga4_id = "G-ABC123XYZ"
        t.meta_pixel_id = "123456789012"
        t.gtm_id = "GTM-ABC1234"
        t.tiktok_pixel_id = "C4ABCDEFGHIJ12345678"
        t.save()
        html = self._home()
        self.assertNotIn("G-ABC123XYZ", html)
        t.ga4_enabled = t.meta_pixel_enabled = t.gtm_enabled = t.tiktok_enabled = True
        t.save()
        html = self._home()
        self.assertIn("gtag('config','G-ABC123XYZ')", html)
        self.assertIn("fbq('init','123456789012')", html)
        self.assertIn("ns.html?id=GTM-ABC1234", html)
        self.assertIn("ttq.load('C4ABCDEFGHIJ12345678')", html)

    def test_tampered_id_not_rendered(self):
        TrackingSettings.objects.update_or_create(pk=1, defaults={"ga4_enabled": True, "ga4_id": "G-x'</script>"})
        self.assertNotIn("G-x'", self._home())


@override_settings(MEDIA_ROOT=MEDIA)
class SeoHeadTests(TestCase):
    def setUp(self):
        cache.clear()

    def _get(self, url="/ua/info/"):
        return self.client.get(url).content.decode()

    def test_default_title_unchanged_and_no_meta_without_settings(self):
        html = self._get("/ua/info/blog/")
        self.assertIn("<title>", html)
        self.assertNotIn('rel="canonical"', html)
        self.assertNotIn('property="og:', html)
        self.assertNotIn('name="description"', html)

    def test_default_title_fallback_when_page_has_none(self):
        from marketing.seo import compose_title

        seo = SeoSettings.load()
        self.assertEqual(str(compose_title("", seo, "ua")), "Центр замків")
        seo.title_default = "Замки Київ"
        seo.title_suffix = "Центр замків"
        self.assertEqual(str(compose_title("", seo, "ua")), "Замки Київ | Центр замків")
        self.assertEqual(str(compose_title("Каталог — Центр замків", seo, "ua")), "Каталог — Центр замків")
        seo.title_default = "Центр замків"
        self.assertEqual(str(compose_title("", seo, "ua")), "Центр замків")

    def test_suffix_applied_on_page(self):
        seo = SeoSettings.load()
        seo.title_suffix = "Бренд"
        seo.save()
        self.assertIn("| Бренд</title>", self._get("/ua/"))

    def test_description_canonical_og(self):
        seo = SeoSettings.load()
        seo.primary_domain = "https://www.zamky.example"
        seo.description_default = "Опис за замовчуванням для сайту замків у Києві, доставка та встановлення."
        seo.description_default_ru = "Описание по умолчанию"
        seo.twitter_site = "zamky"
        seo.save()
        html = self.client.get("/ua/info/?utm_source=x").content.decode()
        self.assertIn('<link rel="canonical" href="https://www.zamky.example/ua/info/">', html)
        self.assertIn('<meta property="og:url" content="https://www.zamky.example/ua/info/">', html)
        self.assertIn('<meta property="og:locale" content="uk_UA">', html)
        self.assertIn('<meta property="og:locale:alternate" content="ru_RU">', html)
        self.assertIn('name="description" content="Опис за замовчуванням', html)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', html)
        self.assertIn('<meta name="twitter:site" content="@zamky">', html)
        self.assertNotIn("utm_source", html.split("</head>")[0])
        ru = self._get("/ru/info/")
        self.assertIn('content="Описание по умолчанию"', ru)
        self.assertIn('<meta property="og:locale" content="ru_RU">', ru)

    def test_verification_and_noindex(self):
        seo = SeoSettings.load()
        seo.google_verification = "abc_DEF-123"
        seo.global_noindex = True
        seo.save()
        html = self._get()
        self.assertIn('<meta name="google-site-verification" content="abc_DEF-123">', html)
        self.assertIn('<meta name="robots" content="noindex, nofollow">', html)
        seo.google_verification = '<meta name="x">'
        with self.assertRaises(ValidationError):
            seo.full_clean()

    def test_jsonld_only_on_home_without_empty_props(self):
        site = SiteSettings.load()
        site.site_name = "Центр замків"
        site.phone_raw = "+380441234567"
        site.instagram_url = "https://instagram.com/zamky"
        site.save()
        seo = SeoSettings.load()
        seo.primary_domain = "https://zamky.example"
        seo.save()
        home = self._get("/ua/")
        self.assertIn('<script type="application/ld+json">', home)
        self.assertIn('"@type":"Organization"', home)
        self.assertIn('"telephone":"+380441234567"', home)
        self.assertIn('"sameAs":["https://instagram.com/zamky"]', home)
        self.assertNotIn('"email"', home)
        self.assertNotIn("SearchAction", home)
        self.assertNotIn("application/ld+json", self._get("/ua/info/"))

    def test_robots_txt(self):
        seo = SeoSettings.load()
        seo.robots_extra = "Disallow: /cart/"
        seo.save()
        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("User-agent: *", body)
        self.assertIn("Disallow: /admin/", body)
        self.assertIn("Disallow: /cart/", body)
        seo.robots_extra = "<script>"
        with self.assertRaises(ValidationError):
            seo.full_clean()

    def test_domain_validation(self):
        seo = SeoSettings.load()
        for bad in ("http://zamky.example", "https://zamky.example/", "zamky.example"):
            seo.primary_domain = bad
            with self.assertRaises(ValidationError):
                seo.full_clean()


class MarketingAdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.user = get_user_model().objects.create_superuser("adm", "adm@example.com", "x-test-pass-1")
        self.client.force_login(self.user)

    def test_admin_pages_open(self):
        feed = ProductFeed.objects.create(name="G", feed_type="google")
        for url in (
            "/admin/marketing/productfeed/",
            f"/admin/marketing/productfeed/{feed.pk}/change/",
            "/admin/marketing/seosettings/",
            "/admin/marketing/trackingsettings/",
            "/admin/pages/homeherosettings/",
        ):
            r = self.client.get(url, follow=True)
            self.assertEqual(r.status_code, 200, url)
        html = self.client.get("/admin/marketing/seosettings/", follow=True).content.decode()
        self.assertIn("закриває ВЕСЬ сайт", html)
        hero = self.client.get("/admin/pages/homeherosettings/", follow=True).content.decode()
        self.assertIn("cta_primary_url", hero)

    def test_enabled_change_logged(self):
        feed = ProductFeed.objects.create(name="G", feed_type="google")
        url = f"/admin/marketing/productfeed/{feed.pk}/change/"
        data = {
            "name": "G", "feed_type": "google", "is_enabled": "on", "slug": feed.slug, "access_token": "",
            "shop_name": "S", "company_name": "", "currency": "UAH", "cache_hours": "3",
            "category_mappings-TOTAL_FORMS": "0", "category_mappings-INITIAL_FORMS": "0",
            "category_mappings-MIN_NUM_FORMS": "0", "category_mappings-MAX_NUM_FORMS": "1000",
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302, r.content[:2000])
        feed.refresh_from_db()
        self.assertTrue(feed.is_enabled)
        self.assertEqual(feed.enabled_changed_by, self.user)
        self.assertIsNotNone(feed.enabled_changed_at)
