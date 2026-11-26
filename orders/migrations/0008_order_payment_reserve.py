from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_sort_order_from_one'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_ref',
            field=models.CharField(blank=True, max_length=64, verbose_name='Референс оплати'),
        ),
        migrations.AddField(
            model_name='order',
            name='reserved_until',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Резерв до'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'Нове'),
                    ('awaiting_payment', 'Очікує оплати'),
                    ('paid', 'Оплачено'),
                    ('confirmed', 'Підтверджено'),
                    ('shipped', 'Відправлено'),
                    ('done', 'Виконано'),
                    ('cancelled', 'Скасовано'),
                ],
                default='new',
                max_length=20,
                verbose_name='Статус',
            ),
        ),
    ]
