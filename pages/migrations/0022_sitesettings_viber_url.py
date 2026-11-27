from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0021_sort_order_from_one'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='viber_url',
            field=models.URLField(blank=True, default='', verbose_name='Viber'),
        ),
    ]
