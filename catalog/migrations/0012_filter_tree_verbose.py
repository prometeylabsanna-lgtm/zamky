from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0011_attribute_verbose_filters'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attributegroup',
            options={
                'ordering': ['sort_order', 'name'],
                'verbose_name': 'Група фільтрів',
                'verbose_name_plural': 'Фільтри',
            },
        ),
        migrations.AlterModelOptions(
            name='attributevalue',
            options={
                'ordering': ['sort_order', 'value'],
                'verbose_name': 'Значення фільтра',
                'verbose_name_plural': 'Фільтри',
                'unique_together': {('attribute', 'slug')},
            },
        ),
    ]
