from django.db import migrations


def fill_filter_sort_orders(apps, schema_editor):
    from catalog.filter_sort import fill_zero_sort_orders

    AttributeGroup = apps.get_model('catalog', 'AttributeGroup')
    Attribute = apps.get_model('catalog', 'Attribute')
    AttributeValue = apps.get_model('catalog', 'AttributeValue')

    fill_zero_sort_orders(AttributeGroup.objects.all(), 'name')
    group_ids = Attribute.objects.values_list('group_id', flat=True).distinct()
    for group_id in group_ids:
        fill_zero_sort_orders(Attribute.objects.filter(group_id=group_id), 'name')
    attr_ids = AttributeValue.objects.values_list('attribute_id', flat=True).distinct()
    for attr_id in attr_ids:
        fill_zero_sort_orders(
            AttributeValue.objects.filter(attribute_id=attr_id), 'value'
        )


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0012_filter_tree_verbose'),
    ]

    operations = [
        migrations.RunPython(fill_filter_sort_orders, noop),
    ]
