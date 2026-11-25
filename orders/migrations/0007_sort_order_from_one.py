from django.db import migrations


def fill_district_sort(apps, schema_editor):
    from catalog.filter_sort import normalize_sort_from_one

    DeliveryDistrict = apps.get_model('orders', 'DeliveryDistrict')
    normalize_sort_from_one(DeliveryDistrict.objects.all(), 'name')


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0006_district_others_title'),
    ]

    operations = [
        migrations.RunPython(fill_district_sort, noop),
    ]
