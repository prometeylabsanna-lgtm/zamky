from django.core.management.base import BaseCommand

from marketing.models import ProductFeed, SeoSettings, TrackingSettings
from marketing.seed import seed_marketing
from pages.models_cms import SiteSettings


class Command(BaseCommand):
    help = "Ідемпотентно створює SEO/пікселі-синглтони і 3 вимкнені фіди."

    def handle(self, *args, **opts):
        stats = seed_marketing(SeoSettings, TrackingSettings, ProductFeed, SiteSettings)
        self.stdout.write(self.style.SUCCESS(f"seed_marketing: {stats}"))
