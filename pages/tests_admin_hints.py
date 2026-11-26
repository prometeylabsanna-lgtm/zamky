from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product
from pages.admin_guidelines import char_rule_for_key, help_for_key
from pages.admin_site_content import SitePageContentForm, load_section_blocks
from pages.site_content_registry import get_section


class AdminHintHelpersTests(TestCase):
    def test_seo_and_icon_hints(self):
        self.assertIn('вкладки браузера', help_for_key('about_seo_title'))
        self.assertIn('пошуку', help_for_key('about_seo_description'))
        self.assertIn('Іконка', help_for_key('audience_1_icon'))
        self.assertNotIn('lock', help_for_key('about_form_topic_lock'))
        self.assertNotIn('info-callout', help_for_key('privacy_body'))

    def test_char_rules(self):
        self.assertEqual(char_rule_for_key('audience_1_title'), {'max': 28})
        self.assertEqual(char_rule_for_key('picker_lead'), {'max': 110})
        self.assertEqual(char_rule_for_key('about_seo_description')['max'], 160)


class CmsSectionHintTests(TestCase):
    def test_visibility_and_char_attrs(self):
        section = get_section('home', 'audience')
        self.assertIsNotNone(section)
        keys = [key for _, key in section.blocks]
        blocks = load_section_blocks(section.page_slug, keys)
        form = SitePageContentForm(section=section, blocks=blocks)
        self.assertIn('не показується', form.fields['section_visible'].help_text)
        title = form.fields['block__home__audience_1_title__text_html']
        self.assertEqual(title.widget.attrs.get('data-char-max'), '28')
        self.assertIn('блоку', form.fields['style_background'].help_text)


class ProductHintTests(TestCase):
    def test_old_price_and_og_help(self):
        from catalog.admin_product_filters import ProductAdminForm

        cat = Category.objects.create(name='Хінти', slug='hints-cat')
        product = Product.objects.create(
            category=cat,
            name='Тест',
            slug='hints-prod',
            sku='HINT-1',
            price=100,
        )
        form = ProductAdminForm(instance=product)
        self.assertIn('закреслена', form.fields['old_price'].help_text)
        self.assertEqual(form.fields['name'].widget.attrs.get('data-char-max'), '80')
        self.assertIn('1200', form.fields['og_image'].help_text)


class AdminHintPagesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser('hintadmin', 'h@ex.com', 'pass12345')
        self.client.force_login(self.user)

    def test_site_settings_logo_hint(self):
        from pages.models_cms import SiteSettings

        obj = SiteSettings.get_solo()
        page = self.client.get(
            reverse('admin:pages_sitesettings_change', args=[obj.pk]),
            HTTP_HOST='127.0.0.1',
        )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'прозорим фоном')
        self.assertContains(page, 'char_hint.js')
