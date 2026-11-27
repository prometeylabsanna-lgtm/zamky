from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from pages.models_cms import SiteSettings
from pages.site_content_registry import build_content_sidebar_groups


class KyivPagesGoneTests(TestCase):
    def test_city_url_is_gone(self):
        page = self.client.get('/ua/kyiv/')
        self.assertEqual(page.status_code, 404)

    def test_district_url_is_gone(self):
        page = self.client.get('/ua/kyiv/obolon/')
        self.assertEqual(page.status_code, 404)

    def test_ru_district_url_is_gone(self):
        page = self.client.get('/ru/kyiv/obolon/?utm_source=ads')
        self.assertEqual(page.status_code, 404)

    def test_cms_district_page_removed(self):
        User = get_user_model()
        User.objects.create_superuser('distadmin', 'dist@example.com', 'pass12345')
        SiteSettings.load()
        client = Client()
        client.force_login(User.objects.get(username='distadmin'))
        groups = build_content_sidebar_groups(admin_prefix='admin/')
        home = next(g for g in groups if g['title'] == 'Головна')
        titles = [item['title'] for item in home['items']]
        self.assertNotIn('Район SEO', titles)
