from django.db import migrations


def fill_catalog_sort(apps, schema_editor):
    from catalog.filter_sort import normalize_sort_from_one

    Category = apps.get_model('catalog', 'Category')
    ProductImage = apps.get_model('catalog', 'ProductImage')
    parent_ids = Category.objects.values_list('parent_id', flat=True).distinct()
    for parent_id in parent_ids:
        normalize_sort_from_one(Category.objects.filter(parent_id=parent_id), 'name')
    product_ids = ProductImage.objects.values_list('product_id', flat=True).distinct()
    for product_id in product_ids:
        normalize_sort_from_one(
            ProductImage.objects.filter(product_id=product_id), 'pk'
        )


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0013_filter_sort_from_one'),
    ]

    operations = [
        migrations.RunPython(fill_catalog_sort, noop),
    ]
