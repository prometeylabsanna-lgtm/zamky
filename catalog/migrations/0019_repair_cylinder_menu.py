from django.db import migrations


def repair_menu(apps, schema_editor):
    from catalog.menu_align import reassign_products_to_menu, sync_category_tree

    sync_category_tree()
    reassign_products_to_menu()


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0018_align_mockup_menu'),
    ]

    operations = [
        migrations.RunPython(repair_menu, noop),
    ]
