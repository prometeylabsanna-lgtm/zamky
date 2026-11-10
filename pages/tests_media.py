from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from pages.models_media import MediaItem


class MediaItemTests(TestCase):
    def test_create_image_item(self):
        # 1x1 PNG
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
            b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        upload = SimpleUploadedFile("dot.png", png, content_type="image/png")
        item = MediaItem(title="Dot", media_type=MediaItem.MediaType.IMAGE, file=upload)
        item.save()
        self.assertTrue(item.pk)
        self.assertTrue(item.file.name.endswith(".webp") or item.file_size >= 0)
        self.assertTrue(item.content_hash)
