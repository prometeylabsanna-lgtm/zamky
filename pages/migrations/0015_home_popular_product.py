from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0007_category_home_card"),
        ("pages", "0014_footer_nav_link"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomePopularProduct",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tab",
                    models.CharField(
                        choices=[
                            ("hits", "Хіти продажу"),
                            ("news", "Новинки"),
                            ("sales", "Знижки"),
                        ],
                        db_index=True,
                        default="hits",
                        max_length=16,
                        verbose_name="Вкладка",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(default=0, verbose_name="Порядок"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Показувати"),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="home_popular_slots",
                        to="catalog.product",
                        verbose_name="Товар",
                    ),
                ),
            ],
            options={
                "verbose_name": "Товар у популярних",
                "verbose_name_plural": "Товари в популярних",
                "ordering": ["tab", "sort_order", "pk"],
            },
        ),
        migrations.AddConstraint(
            model_name="homepopularproduct",
            constraint=models.UniqueConstraint(
                fields=("tab", "product"),
                name="uniq_home_popular_tab_product",
            ),
        ),
    ]
