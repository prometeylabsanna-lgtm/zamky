from django.db import migrations


def dedupe_and_sync_nav(apps, schema_editor):
    from catalog.menu_align import reassign_products_to_menu, sync_category_tree
    from pages.footer_nav import sync_default_footer_nav
    from pages.header_nav import sync_default_header_nav

    sync_category_tree()
    reassign_products_to_menu()
    sync_default_header_nav()
    sync_default_footer_nav()


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0019_repair_cylinder_menu'),
        ('pages', '0021_sort_order_from_one'),
    ]

    operations = [
        migrations.RunPython(dedupe_and_sync_nav, noop),
    ]
