from django.db import migrations


def apply_mockup_listing(apps, schema_editor):
    from catalog.menu_align import reassign_products_to_menu, sync_category_tree
    from catalog.mockup_catalog import sync_mockup_products

    sync_category_tree()
    reassign_products_to_menu()
    sync_mockup_products()


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0020_dedupe_menu_children'),
    ]

    operations = [
        migrations.RunPython(apply_mockup_listing, noop),
    ]
