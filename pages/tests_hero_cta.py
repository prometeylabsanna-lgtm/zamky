from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from pages.models_cms import HeroSlide


@override_settings(CMS_ALLOW_STATIC_FALLBACK=True)
class HeroCtaTests(TestCase):
    def setUp(self):
        cache.clear()
        HeroSlide.objects.all().delete()  # тестова БД
        self.s1 = HeroSlide.objects.create(
            alt_text="Слайд 1",
            static_fallback="img/v2/hero/slide-home.webp",
            sort_order=1,
            show_secondary=True,
        )
        self.s2 = HeroSlide.objects.create(
            alt_text="Слайд 2",
            static_fallback="img/v2/hero/slide-promo.webp",
            sort_order=2,
        )

    def _cta_html(self, url="/ua/"):
        html = self.client.get(url).content.decode()
        start = html.index('class="home-hero__overlay"')
        return html[start: html.index("</section>", start)]

    def test_empty_labels_hide_buttons(self):
        cta = self._cta_html()
        self.assertEqual(cta.count("data-hero-cta"), 2)
        self.assertNotIn("Перейти до каталогу", cta)
        self.assertNotIn("Підібрати замок за 2 хв", cta)
        self.assertNotIn("home-hero__cta-link", cta)
        self.s1.cta_primary_label = "Перейти до каталогу"
        self.s1.cta_secondary_label = "Підібрати замок за 2 хв"
        self.s1.show_secondary = True
        self.s1.save()
        cta = self._cta_html()
        self.assertEqual(cta.count("Перейти до каталогу"), 1)
        self.assertEqual(cta.count("Підібрати замок за 2 хв"), 1)
        self.assertIn('href="/ua/catalog/"', cta)
        self.assertIn('href="#picker"', cta)
        self.assertEqual(cta.count("data-hero-cta hidden"), 1)

    def test_custom_per_slide(self):
        self.s2.cta_primary_label = "Акція −20%"
        self.s2.cta_primary_label_ru = "Акция −20%"
        self.s2.cta_primary_url = "/ua/catalog/cyl/"
        self.s2.cta_secondary_label = "Подзвонити"
        self.s2.cta_secondary_url = "tel:+380441234567"
        self.s2.show_secondary = True
        self.s2.save()
        cta = self._cta_html()
        self.assertNotIn("Перейти до каталогу", cta)
        self.assertIn("Акція −20%", cta)
        self.assertIn('href="/ua/catalog/cyl/"', cta)
        self.assertIn('href="tel:+380441234567"', cta)
        self.assertIn("Акция −20%", self._cta_html("/ru/"))

    def test_url_validation(self):
        for ok in ("/ua/catalog/", "#picker", "https://example.com/x", "tel:+380441234567"):
            self.s1.cta_primary_url = ok
            self.s1.full_clean()
        for bad in ("javascript:alert(1)", "//evil.com", "http://x.com", "catalog"):
            self.s1.cta_primary_url = bad
            with self.assertRaises(ValidationError):
                self.s1.full_clean()

    def test_admin_formset_saves_and_validates_cta(self):
        from pages.admin_hero_slides import build_hero_slide_formset

        fs = build_hero_slide_formset()
        data = {k: v for k, v in fs.management_form.initial.items()}
        data = {f"hero_slides-{k}": v for k, v in data.items()}
        forms = fs.initial_forms
        data["hero_slides-TOTAL_FORMS"] = str(len(forms))
        for i, form in enumerate(forms):
            for name, field in form.fields.items():
                val = form.instance.pk if name == "id" else form.initial.get(name, "")
                if name == "is_active":
                    if val:
                        data[f"hero_slides-{i}-{name}"] = "on"
                    continue
                data[f"hero_slides-{i}-{name}"] = "" if val is None else val
        data["hero_slides-0-cta_primary_label"] = "Нова кнопка"
        data["hero_slides-0-cta_primary_url"] = "javascript:alert(1)"
        bad = build_hero_slide_formset(data=data)
        self.assertFalse(bad.is_valid())
        data["hero_slides-0-cta_primary_url"] = "/ua/catalog/"
        good = build_hero_slide_formset(data=data)
        self.assertTrue(good.is_valid(), good.errors)
        good.save()
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.cta_primary_label, "Нова кнопка")

    def test_admin_hero_cta_columns_and_checks(self):
        from django.contrib.auth import get_user_model
        from django.test import Client
        from django.urls import reverse

        User = get_user_model()
        User.objects.create_superuser("heroadmin", "hero@example.com", "pass12345")
        client = Client()
        client.force_login(User.objects.get(username="heroadmin"))
        url = reverse("admin:pages_homeherosettings_changelist")
        response = client.get(url)
        if response.status_code == 302:
            response = client.get(response["Location"])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hero-slide-row__cta-col")
        self.assertContains(response, "hero-slide-row__check")
        self.assertContains(response, "js/admin/image_preview.js")
        self.assertContains(response, "js/admin/hero_slides.js")
        self.assertContains(response, "data-hero-add")
        self.assertContains(response, "data-hero-empty")
        self.assertContains(response, "hero_slides-__prefix__-alt_text")
        self.assertContains(response, "hero_slides-__prefix__-headline")
        html = response.content.decode()
        start = html.index("data-hero-slides")
        end = html.index("</fieldset>", start)
        self.assertIn('name="hero_slides-TOTAL_FORMS"', html[start:end])

    def test_hero_overlay_is_html_not_image_only(self):
        self.s1.cta_primary_label = "До каталогу"
        self.s1.save()
        html = self.client.get("/ua/").content.decode()
        self.assertIn("home-hero__overlay", html)
        self.assertIn("home-hero__cta-link", html)
        self.assertIn("home-hero__badge", html)
        self.assertIn("css/home-hero.css", html)
        self.assertIn("css/home-hero-2.css", html)

    def test_hero_kind_and_wide_cta(self):
        from pages.hero_slides import ensure_default_hero_slides

        HeroSlide.objects.all().delete()
        ensure_default_hero_slides()
        html = self.client.get("/ua/").content.decode()
        self.assertIn('data-hero-kind="home"', html)
        self.assertIn('data-hero-kind="promo"', html)
        self.assertIn('data-hero-kind="install"', html)
        self.assertIn('data-hero-kind="brands"', html)
        self.assertIn("home-hero__actions--single", html)
        self.assertIn("home-hero__cta-spark", html)
        self.assertIn("heroPromoSpark", html)


@override_settings(CMS_ALLOW_STATIC_FALLBACK=False)
class HeroStaticFallbackOnProdTests(TestCase):
    def setUp(self):
        cache.clear()
        HeroSlide.objects.all().delete()

    def test_empty_db_seeds_default_webps(self):
        from pages.hero_slides import get_hero_slides

        slides = get_hero_slides("ua")
        self.assertGreaterEqual(len(slides), 4)
        self.assertTrue(any("slide-home.webp" in (s.image or "") for s in slides))
        html = self.client.get("/ua/").content.decode()
        self.assertIn("data-hero-slide", html)
        self.assertIn("slide-home.webp", html)
        self.assertIn("img src=", html)
        self.assertIn('rel="preload"', html)
        self.assertIn("as=\"image\"", html)
        self.assertIn("slide-home-800.webp", html)
        self.assertIn("data-src=", html)
        self.assertIn("(min-width: 1440px) 1360px, 100vw", html)
        self.assertNotIn("1310px", html)
        self.assertNotIn("fonts.googleapis.com", html)
        self.assertIn("inter-cyrillic.woff2", html)
        self.assertIn("logo.webp", html)
        self.assertIn("p2_14.webp", html)

    def test_blank_cms_rows_backfill_static(self):
        from pages.hero_slides import get_hero_slides

        HeroSlide.objects.create(alt_text="порожній", is_active=True, sort_order=0)
        slides = get_hero_slides("ua")
        self.assertGreaterEqual(len(slides), 1)
        self.assertIn("slide-home.webp", slides[0].image or "")
        row = HeroSlide.objects.order_by("sort_order", "pk").first()
        self.assertEqual(row.static_fallback, "img/v2/hero/slide-home.webp")
        html = self.client.get("/ua/").content.decode()
        self.assertIn("slide-home.webp", html)
