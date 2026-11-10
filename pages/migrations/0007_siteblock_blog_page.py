from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0006_pagestyle"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pagestyle",
            name="page",
            field=models.CharField(
                choices=[
                    ("home", "Головна"),
                    ("site", "Сайт"),
                    ("about", "Про нас"),
                    ("delivery", "Доставка"),
                    ("warranty", "Гарантія"),
                    ("returns", "Обмін"),
                    ("install", "Установка"),
                    ("promos", "Акції"),
                    ("offer", "Оферта"),
                    ("privacy", "Політика"),
                    ("blog", "Блог"),
                    ("catalog", "Каталог"),
                    ("product", "Товар"),
                    ("cart", "Кошик"),
                    ("checkout", "Оформлення"),
                    ("wishlist", "Обране"),
                ],
                max_length=32,
                unique=True,
                verbose_name="Сторінка",
            ),
        ),
        migrations.AlterField(
            model_name="siteblock",
            name="page",
            field=models.CharField(
                choices=[
                    ("home", "Головна"),
                    ("site", "Сайт"),
                    ("about", "Про нас"),
                    ("delivery", "Доставка"),
                    ("warranty", "Гарантія"),
                    ("returns", "Обмін"),
                    ("install", "Установка"),
                    ("promos", "Акції"),
                    ("offer", "Оферта"),
                    ("privacy", "Політика"),
                    ("blog", "Блог"),
                    ("catalog", "Каталог"),
                    ("product", "Товар"),
                    ("cart", "Кошик"),
                    ("checkout", "Оформлення"),
                    ("wishlist", "Обране"),
                ],
                max_length=32,
                verbose_name="Сторінка",
            ),
        ),
    ]
