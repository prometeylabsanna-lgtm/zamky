import tempfile
from io import BytesIO
from shutil import rmtree

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from PIL import Image

from pages.models_extra import PhotoPickImage, PhotoPickRequest


def _tiny_jpeg(name='shot.jpg'):
    buf = BytesIO()
    Image.new('RGB', (2, 2), (200, 30, 30)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


@override_settings(ALLOWED_HOSTS=['*'])
class PhotoPickUploadTests(TestCase):
    def setUp(self):
        self._media = tempfile.mkdtemp(prefix='picker-test-')
        media_patch = override_settings(MEDIA_ROOT=self._media)
        media_patch.enable()
        self.addCleanup(media_patch.disable)
        self.addCleanup(lambda: rmtree(self._media, ignore_errors=True))

    def tearDown(self):
        translation.deactivate_all()

    def test_rejects_html_as_image(self):
        with translation.override('ua'):
            self.client.get(reverse('catalog:home'))
        fake = SimpleUploadedFile(
            'x.jpg',
            b'<html><script>alert(1)</script></html>',
            content_type='image/jpeg',
        )
        response = self.client.post(
            reverse('pages:photo_pick'),
            {
                'phone': '+380670000003',
                'channel': 'call',
                'photos': fake,
            },
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PhotoPickRequest.objects.count(), 0)
        self.assertEqual(PhotoPickImage.objects.count(), 0)
        self.assertContains(response, 'JPEG')

    def test_converts_heic_to_jpeg(self):
        try:
            from pillow_heif import register_heif_opener
        except ImportError:
            self.skipTest('pillow-heif is not installed')
        register_heif_opener()
        buf = BytesIO()
        Image.new('RGB', (2, 2), (10, 80, 200)).save(buf, format='HEIF')
        heic = SimpleUploadedFile(
            'door.heic',
            buf.getvalue(),
            content_type='image/heic',
        )
        with translation.override('ua'):
            self.client.get(reverse('catalog:home'))
        response = self.client.post(
            reverse('pages:photo_pick'),
            {
                'phone': '+380670000005',
                'channel': 'call',
                'photos': heic,
            },
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PhotoPickRequest.objects.count(), 1)
        img = PhotoPickImage.objects.get()
        stored = img.image.name.lower()
        self.assertTrue(img.image.name.startswith('picker/'))
        self.assertTrue(stored.endswith(('.jpg', '.jpeg', '.webp')))
        self.assertNotIn('door.heic', stored)

    def test_stores_uuid_jpeg_name(self):
        with translation.override('ua'):
            self.client.get(reverse('catalog:home'))
        response = self.client.post(
            reverse('pages:photo_pick'),
            {
                'phone': '+380670000004',
                'channel': 'call',
                'photos': _tiny_jpeg('evil.jpg'),
            },
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PhotoPickRequest.objects.count(), 1)
        img = PhotoPickImage.objects.get()
        stored = img.image.name.lower()
        self.assertTrue(img.image.name.startswith('picker/'))
        self.assertTrue(stored.endswith(('.jpg', '.jpeg', '.png', '.webp')))
        self.assertNotIn('evil', stored)
