from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0014_sort_order_from_one'),
    ]

    operations = [
        migrations.CreateModel(
            name='FamilyColorSwatch',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'color_code',
                    models.CharField(
                        choices=[
                            ('G', 'Латунь'),
                            ('N', 'Нікель'),
                            ('B', 'Чорний'),
                        ],
                        max_length=8,
                        verbose_name='Колір серцевини',
                    ),
                ),
                (
                    'image',
                    models.ImageField(
                        blank=True,
                        help_text=(
                            'Фото кнопки кольору на сторінці товару. '
                            'Порожньо — суцільний колір.'
                        ),
                        upload_to='families/swatches/',
                        verbose_name='Плашка',
                    ),
                ),
                (
                    'family',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='color_swatches',
                        to='catalog.productfamily',
                        verbose_name='Сімʼя',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Плашка кольору',
                'verbose_name_plural': 'Плашки кольорів',
                'ordering': ['id'],
                'unique_together': {('family', 'color_code')},
            },
        ),
    ]
