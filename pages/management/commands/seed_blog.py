from django.core.management.base import BaseCommand
from django.utils.text import slugify

from pages.blog_defaults import POSTS
from pages.models import BlogPost


class Command(BaseCommand):
    help = 'Створює демо-статті блогу (4 записи з Design-v2).'

    def handle(self, *args, **options):
        created = 0
        for row in POSTS:
            slug = row.get('slug') or slugify(row['title']) or 'post'
            _, was_created = BlogPost.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': row['title'],
                    'excerpt': row['excerpt'],
                    'body': row['body'],
                    'sort_order': row['sort_order'],
                    'is_published': True,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Блог: {created} нових, усього {BlogPost.objects.count()} статей.'
            )
        )
