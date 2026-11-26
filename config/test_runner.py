import shutil
import tempfile

from django.conf import settings
from django.test.runner import DiscoverRunner


class TempMediaDiscoverRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._orig_media_root = settings.MEDIA_ROOT
        self._media_root = tempfile.mkdtemp(prefix='zamky-test-media-')
        settings.MEDIA_ROOT = self._media_root

    def teardown_test_environment(self, **kwargs):
        media = getattr(self, '_media_root', None)
        if hasattr(self, '_orig_media_root'):
            settings.MEDIA_ROOT = self._orig_media_root
        if media:
            shutil.rmtree(media, ignore_errors=True)
        super().teardown_test_environment(**kwargs)
