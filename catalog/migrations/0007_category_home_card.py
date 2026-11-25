from django.db import migrations, models


def copy_home_subs(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    SiteBlock = apps.get_model("pages", "SiteBlock")
    cats = list(
        Category.objects.filter(parent__isnull=True).order_by("sort_order", "name", "pk")
    )
    for i, cat in enumerate(cats[:6], start=1):
        block = SiteBlock.objects.filter(page="home", key=f"categories_{i}_sub").first()
        if block is None:
            continue
        updates = []
        ua = (block.text_html or "").strip()
        ru = (block.text_html_ru or "").strip()
        if ua and not (cat.home_subtitle or "").strip():
            cat.home_subtitle = ua
            updates.append("home_subtitle")
        if ru and not (cat.home_subtitle_ru or "").strip():
            cat.home_subtitle_ru = ru
            updates.append("home_subtitle_ru")
        if updates:
            cat.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0006_rename_facets_to_catalog_filters"),
        ("pages", "0009_heroslide_overlay"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="name_ru",
            field=models.CharField(
                blank=True, default="", max_length=200, verbose_name="Назва (RU)"
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="home_subtitle",
            field=models.CharField(
                blank=True,
                default="",
                max_length=180,
                verbose_name="Підпис на головній",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="home_subtitle_ru",
            field=models.CharField(
                blank=True,
                default="",
                max_length=180,
                verbose_name="Підпис на головній (RU)",
            ),
        ),
        migrations.RunPython(copy_home_subs, migrations.RunPython.noop),
    ]
