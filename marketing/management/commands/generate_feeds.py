"""Генерує (і прогріває кеш) увімкнених товарних фідів.

    python manage.py generate_feeds                 # усі увімкнені
    python manage.py generate_feeds --slug feed-…   # один
    python manage.py generate_feeds --output /tmp/feeds --base-url https://example.com
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from marketing.feeds import get_feed_payload, resolve_base_url
from marketing.models import ProductFeed


class Command(BaseCommand):
    help = "Згенерувати товарні фіди (Google/Facebook RSS, Prom YML) і прогріти кеш."

    def add_arguments(self, parser):
        parser.add_argument("--slug", help="Лише фід з цим слагом")
        parser.add_argument("--include-disabled", action="store_true", help="Також вимкнені (лише для перевірки у файл)")
        parser.add_argument("--output", help="Тека, куди записати <slug>.xml")
        parser.add_argument("--base-url", default="", help="Якщо в SEO-налаштуваннях не заданий основний домен")

    def handle(self, *args, **opts):
        qs = ProductFeed.objects.all()
        if not opts["include_disabled"]:
            qs = qs.filter(is_enabled=True)
        if opts["slug"]:
            qs = qs.filter(slug=opts["slug"])
        base = resolve_base_url() or opts["base_url"].rstrip("/")
        if not base:
            raise CommandError("Немає основного домену: заповніть Маркетинг → SEO або передайте --base-url.")
        out_dir = Path(opts["output"]) if opts["output"] else None
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for feed in qs:
            payload = get_feed_payload(feed, base, force=True)
            count += 1
            line = f"{feed.slug} [{feed.feed_type}]: у фіді {payload.included}, виключено {payload.excluded} {payload.reasons}"
            if out_dir:
                path = out_dir / f"{feed.slug}.xml"
                path.write_bytes(payload.body)
                line += f" → {path}"
            self.stdout.write(line)
        self.stdout.write(self.style.SUCCESS(f"Фідів: {count}"))
