from django.db import migrations, models


def convert_blog_bodies(apps, schema_editor):
    from pages.legal_body import plain_text_to_html

    BlogPost = apps.get_model("pages", "BlogPost")
    for post in BlogPost.objects.all():
        html = plain_text_to_html(post.body or "")
        if html != (post.body or ""):
            post.body = html
            post.save(update_fields=["body"])


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0017_legal_body"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blogpost",
            name="body",
            field=models.TextField(verbose_name="Текст статті"),
        ),
        migrations.AlterModelOptions(
            name="blogpost",
            options={
                "ordering": ["sort_order", "-created_at"],
                "verbose_name": "Стаття",
                "verbose_name_plural": "Список статей",
            },
        ),
        migrations.RunPython(convert_blog_bodies, migrations.RunPython.noop),
    ]
