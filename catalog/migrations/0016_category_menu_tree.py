from django.db import migrations, models


def seed_menu_tree(apps, schema_editor):
    from catalog.category_tree import ensure_category_tree

    ensure_category_tree()


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0015_family_color_swatch'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='show_in_menu',
            field=models.BooleanField(
                default=True, verbose_name='Показувати в меню'
            ),
        ),
        migrations.RunPython(seed_menu_tree, noop),
    ]
