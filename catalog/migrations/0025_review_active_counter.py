from django.db import migrations, models
from django.db.models import Count


def activate_and_sync_counts(apps, schema_editor):
    Review = apps.get_model('catalog', 'Review')
    Product = apps.get_model('catalog', 'Product')
    counted = {
        row['product_id']: row['n']
        for row in Review.objects.filter(is_published=True)
        .values('product_id')
        .annotate(n=Count('id'))
    }
    for product_id, n in counted.items():
        Product.objects.filter(pk=product_id).update(reviews_count=n)
    if counted:
        Product.objects.exclude(pk__in=counted).update(reviews_count=0)
    else:
        Product.objects.update(reviews_count=0)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0024_product_reviews'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='reviews_count',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Рахується автоматично з активних відгуків.',
                verbose_name='Кількість відгуків',
            ),
        ),
        migrations.AlterField(
            model_name='review',
            name='is_published',
            field=models.BooleanField(
                default=True,
                help_text='Без галочки відгук не видно на сайті.',
                verbose_name='Активний',
            ),
        ),
        migrations.RunPython(activate_and_sync_counts, migrations.RunPython.noop),
    ]
