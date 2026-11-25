from django.db import migrations, models


def fill_ru(apps, schema_editor):
    from catalog.filter_i18n import fill_filter_translations

    fill_filter_translations(
        group_model=apps.get_model('catalog', 'AttributeGroup'),
        attr_model=apps.get_model('catalog', 'Attribute'),
        value_model=apps.get_model('catalog', 'AttributeValue'),
    )


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0008_product_color_code_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='attributegroup',
            name='name_ru',
            field=models.CharField(
                blank=True, default='', max_length=120, verbose_name='Назва (RU)'
            ),
        ),
        migrations.AddField(
            model_name='attribute',
            name='name_ru',
            field=models.CharField(
                blank=True, default='', max_length=120, verbose_name='Назва (RU)'
            ),
        ),
        migrations.AddField(
            model_name='attributevalue',
            name='value_ru',
            field=models.CharField(
                blank=True, default='', max_length=200, verbose_name='Значення (RU)'
            ),
        ),
        migrations.RunPython(fill_ru, migrations.RunPython.noop),
    ]
