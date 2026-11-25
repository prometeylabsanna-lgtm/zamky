from django.db import migrations, models


def fill_measure(apps, schema_editor):
    from catalog.measure_guide import apply_default_measure

    Category = apps.get_model('catalog', 'Category')
    for cat in Category.objects.all():
        changed = apply_default_measure(cat)
        if changed:
            cat.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0009_filter_i18n'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='measure_title',
            field=models.CharField(
                blank=True,
                default='',
                help_text='На картці товару біля розміру. Порожнє — з батьківської категорії.',
                max_length=160,
                verbose_name='Кнопка підказки',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='measure_title_ru',
            field=models.CharField(
                blank=True,
                default='',
                max_length=160,
                verbose_name='Кнопка підказки (RU)',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='measure_text',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Пояснення після натискання кнопки. Порожнє — з батьківської категорії.',
                verbose_name='Текст підказки',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='measure_text_ru',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Текст підказки (RU)',
            ),
        ),
        migrations.RunPython(fill_measure, migrations.RunPython.noop),
    ]
