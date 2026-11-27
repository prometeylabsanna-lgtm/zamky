from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_order_np_city_ref_order_np_warehouse_ref_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='district',
        ),
        migrations.DeleteModel(
            name='DeliveryDistrict',
        ),
        migrations.AddField(
            model_name='order',
            name='city',
            field=models.CharField(blank=True, default='', max_length=120, verbose_name='Місто'),
        ),
    ]
