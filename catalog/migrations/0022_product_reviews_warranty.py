from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0021_mockup_type_listing'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='reviews_count',
            field=models.PositiveIntegerField(
                default=0, verbose_name='Кількість відгуків'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='warranty_months',
            field=models.PositiveSmallIntegerField(
                default=12, verbose_name='Гарантія, місяців'
            ),
        ),
    ]
