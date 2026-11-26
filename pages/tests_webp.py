import io
import tempfile
from shutil import rmtree

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from catalog.models import Category
from pages.image_webp import (
    MAX_SIDE,
    card_image_url,
    card_sidecar_name,
    encode_raster_to_webp,
    encode_resized_webp,
    skip_stored_name,
)
from pages.models_media import MediaItem


def _jpeg_bytes(width=32, height=24, *, orientation=None):
    img = Image.new('RGB', (width, height), (30, 90, 160))
    buf = io.BytesIO()
    if orientation:
        exif = img.getexif()
        exif[274] = orientation
        img.save(buf, format='JPEG', quality=95, exif=exif)
    else:
        img.save(buf, format='JPEG', quality=95)
    return buf.getvalue()


def _png_alpha_bytes():
    img = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
    img.putpixel((5, 5), (0, 220, 40, 255))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


class WebpConversionTests(TestCase):
    def setUp(self):
        self._media = tempfile.mkdtemp(prefix='webp-test-')
        patch = override_settings(MEDIA_ROOT=self._media)
        patch.enable()
        self.addCleanup(patch.disable)
        self.addCleanup(lambda: rmtree(self._media, ignore_errors=True))

    def test_encode_skips_svg_and_gif(self):
        self.assertTrue(skip_stored_name('icon.svg'))
        self.assertTrue(skip_stored_name('pic.webp'))
        self.assertFalse(skip_stored_name('pic.jpg'))
        self.assertIsNone(encode_raster_to_webp(b'<svg></svg>', source_name='icon.svg'))
        gif = (
            b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
            b'\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00'
            b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )
        self.assertIsNone(encode_raster_to_webp(gif, source_name='a.gif'))

    def test_encode_skips_optimal_webp(self):
        buf = io.BytesIO()
        Image.new('RGB', (8, 8), (1, 2, 3)).save(buf, format='WEBP', quality=88)
        data = buf.getvalue()
        self.assertIsNone(encode_raster_to_webp(data, source_name='ok.webp'))

    def test_exif_transpose_and_resize(self):
        raw = _jpeg_bytes(40, 20, orientation=6)
        encoded = encode_raster_to_webp(raw, source_name='phone.jpg')
        self.assertIsNotNone(encoded)
        _data, width, height = encoded
        self.assertEqual((width, height), (20, 40))

        huge = _jpeg_bytes(3000, 100)
        encoded = encode_raster_to_webp(huge, source_name='wide.jpg')
        self.assertIsNotNone(encoded)
        _data, width, height = encoded
        self.assertEqual(width, MAX_SIDE)
        self.assertLessEqual(height, 100)

    def test_admin_upload_jpeg_becomes_webp(self):
        upload = SimpleUploadedFile('door.jpg', _jpeg_bytes(), content_type='image/jpeg')
        cat = Category.objects.create(name='WebP', slug='webp-upload', logo=upload)
        self.assertTrue(cat.logo.name.endswith('.webp'))
        with cat.logo.open('rb') as fh:
            img = Image.open(fh)
            self.assertEqual(img.format, 'WEBP')

    def test_alpha_png_keeps_transparency(self):
        upload = SimpleUploadedFile(
            'badge.png', _png_alpha_bytes(), content_type='image/png'
        )
        cat = Category.objects.create(name='Alpha', slug='webp-alpha', logo=upload)
        with cat.logo.open('rb') as fh:
            img = Image.open(fh)
            img.load()
        self.assertEqual(img.mode, 'RGBA')
        self.assertEqual(img.getpixel((0, 0))[3], 0)
        self.assertEqual(img.getpixel((5, 5))[3], 255)

    def test_replace_upload_deletes_old_file(self):
        first = SimpleUploadedFile('a.jpg', _jpeg_bytes(), content_type='image/jpeg')
        cat = Category.objects.create(name='Swap', slug='webp-swap', logo=first)
        old_name = cat.logo.name
        self.assertTrue(default_storage.exists(old_name))
        second = SimpleUploadedFile('b.png', _png_alpha_bytes(), content_type='image/png')
        cat.logo = second
        cat.save()
        self.assertTrue(cat.logo.name.endswith('.webp'))
        self.assertNotEqual(cat.logo.name, old_name)
        self.assertFalse(default_storage.exists(old_name))

    def test_command_dry_run_then_convert_idempotent(self):
        jpeg = _jpeg_bytes(64, 48)
        path = default_storage.save('categories/legacy.jpg', ContentFile(jpeg))
        cat = Category(name='Legacy', slug='webp-legacy')
        cat.logo.name = path
        cat.save()
        self.assertTrue(cat.logo.name.endswith('.jpg'))

        out = io.StringIO()
        call_command(
            'convert_images_webp',
            dry_run=True,
            model='catalog.Category',
            stdout=out,
        )
        cat.refresh_from_db()
        self.assertTrue(cat.logo.name.endswith('.jpg'))
        self.assertIn('DRY-RUN', out.getvalue())
        self.assertTrue(default_storage.exists(path))

        call_command('convert_images_webp', model='catalog.Category')
        cat.refresh_from_db()
        self.assertTrue(cat.logo.name.endswith('.webp'))
        self.assertFalse(default_storage.exists(path))

        out = io.StringIO()
        call_command('convert_images_webp', model='catalog.Category', stdout=out)
        self.assertIn('converted=0', out.getvalue())

    def test_media_item_png_to_webp(self):
        upload = SimpleUploadedFile('dot.png', _png_alpha_bytes(), content_type='image/png')
        item = MediaItem(title='Dot', media_type=MediaItem.MediaType.IMAGE, file=upload)
        item.save()
        self.assertTrue(item.file.name.endswith('.webp'))
        self.assertTrue(item.content_hash)
        self.assertEqual(item.width, 10)

    def test_upload_writes_card_sidecar(self):
        upload = SimpleUploadedFile(
            'wide.jpg', _jpeg_bytes(900, 600), content_type='image/jpeg'
        )
        cat = Category.objects.create(name='Card', slug='webp-card', logo=upload)
        sidecar = card_sidecar_name(cat.logo.name)
        self.assertTrue(sidecar.endswith('-card.webp'))
        self.assertTrue(default_storage.exists(sidecar))
        url = card_image_url(cat.logo)
        self.assertIn('-card.webp', url)
        encoded = encode_resized_webp(
            _jpeg_bytes(900, 600), max_side=480, source_name='wide.jpg'
        )
        self.assertIsNotNone(encoded)
        _data, width, height = encoded
        self.assertEqual(width, 480)
        self.assertEqual(height, 320)

    def test_admin_category_preview_uses_webp_url(self):
        User = get_user_model()
        user = User.objects.create_superuser('webpadmin', 'w@ex.com', 'pass12345')
        self.client.force_login(user)
        upload = SimpleUploadedFile('door.jpg', _jpeg_bytes(), content_type='image/jpeg')
        cat = Category.objects.create(name='AdminPrev', slug='webp-admin-prev', logo=upload)
        page = self.client.get(
            reverse('admin:catalog_category_change', args=[cat.pk]),
            HTTP_HOST='127.0.0.1',
        )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, '.webp')
        self.assertContains(page, 'admin-img-preview')
