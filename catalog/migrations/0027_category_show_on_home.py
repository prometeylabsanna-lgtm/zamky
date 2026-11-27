from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0026_remove_product_family"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="show_on_home",
            field=models.BooleanField(default=True, verbose_name="Показувати на головній"),
        ),
    ]
