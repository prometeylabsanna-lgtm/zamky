from django.db import migrations


def align_mockup_menu(apps, schema_editor):
    from catalog.menu_align import reassign_products_to_menu, sync_category_tree
    from pages.footer_nav import sync_default_footer_nav
    from pages.header_nav import sync_default_header_nav

    sync_category_tree()
    # Живі моделі мають колонки з пізніших міграцій (напр. reviews_avg) — на чистій базі товарів немає, пропускаємо.
    if apps.get_model('catalog', 'Product').objects.exists():
        reassign_products_to_menu()
    sync_default_header_nav()
    sync_default_footer_nav()
    SiteBlock = apps.get_model('pages', 'SiteBlock')
    SiteBlock.objects.filter(
        page='site', key='header_catalog_label', text_html='Каталог'
    ).update(text_html='Каталог товарів')
    SiteBlock.objects.filter(
        page='site', key='header_catalog_label', text_html_ru='Каталог'
    ).update(text_html_ru='Каталог товаров')


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0017_reassign_category_leaves'),
        ('pages', '0021_sort_order_from_one'),
    ]

    operations = [
        migrations.RunPython(align_mockup_menu, noop),
    ]
