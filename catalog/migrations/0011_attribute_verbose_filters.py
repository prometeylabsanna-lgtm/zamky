from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0010_category_measure_guide'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attribute',
            options={
                'ordering': ['sort_order', 'name'],
                'verbose_name': 'Фільтр',
                'verbose_name_plural': 'Фільтри',
            },
        ),
    ]
