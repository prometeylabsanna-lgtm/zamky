from django.db import migrations


def sync_demo_posts(apps, schema_editor):
    from pages.blog_defaults import POSTS
    from pages.legal_body import clean_legal_fragment

    BlogPost = apps.get_model("pages", "BlogPost")
    by_slug = {row["slug"]: row for row in POSTS}
    for post in BlogPost.objects.all():
        row = by_slug.get(post.slug)
        fields = ["title", "excerpt", "body"]
        post.title = clean_legal_fragment(post.title)
        post.excerpt = clean_legal_fragment(post.excerpt)
        if row:
            post.title = row["title"]
            post.excerpt = row["excerpt"]
            post.body = row["body"]
            post.sort_order = row["sort_order"]
            fields.append("sort_order")
        post.save(update_fields=fields)


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0018_blog_body_html"),
    ]

    operations = [
        migrations.RunPython(sync_demo_posts, migrations.RunPython.noop),
    ]
