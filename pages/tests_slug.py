from django.test import SimpleTestCase, TestCase

from catalog.models import Attribute, AttributeValue
from pages.slug_utils import ensure_unique_slug, should_rebuild_slug, slug_seed


class SlugSeedTests(SimpleTestCase):
    def test_keeps_latin_and_digits(self):
        self.assertEqual(slug_seed('ABARO B100'), 'abaro-b100')

    def test_ukrainian_not_stripped_to_digit(self):
        self.assertEqual(slug_seed('тип2'), 'typ2')
        self.assertEqual(slug_seed('Тип'), 'typ')
        self.assertEqual(slug_seed('Безпека та комплектація'), 'bezpeka-ta-komplektatsiia')

    def test_fallback_when_empty(self):
        self.assertEqual(slug_seed('***', 'value'), 'value')

    def test_rebuilds_stripped_cyrillic_digit(self):
        self.assertTrue(should_rebuild_slug('тип2', '2', 'value'))
        self.assertFalse(should_rebuild_slug('5', '5', 'value'))
        self.assertFalse(should_rebuild_slug('typ2', 'typ2', 'value'))


class UniqueSlugTests(TestCase):
    def test_filter_value_slug_from_cyrillic(self):
        attr = Attribute.objects.create(name='Тип', slug='typ-test')
        slug = ensure_unique_slug(
            AttributeValue,
            'тип2',
            extra_filter={'attribute_id': attr.pk},
            fallback='value',
        )
        self.assertEqual(slug, 'typ2')
