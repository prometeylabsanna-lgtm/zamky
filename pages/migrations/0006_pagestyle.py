from django.db import migrations, models


def seed_page_styles(apps, schema_editor):
    PageStyle = apps.get_model("pages", "PageStyle")
    SiteBlock = apps.get_model("pages", "SiteBlock")
    # SiteBlock.Page choices are on the model field
    field = SiteBlock._meta.get_field("page")
    for value, _label in field.choices:
        PageStyle.objects.get_or_create(page=value)


def unseed_page_styles(apps, schema_editor):
    PageStyle = apps.get_model("pages", "PageStyle")
    PageStyle.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0005_uk_labels_and_timestamps"),
    ]

    operations = [
        migrations.CreateModel(
            name="PageStyle",
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
                    "page",
                    models.CharField(
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
                (
                    "background_color",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="HEX. Порожнє — як зараз на сайті.",
                        max_length=32,
                        verbose_name="Колір фону",
                    ),
                ),
                (
                    "text_color",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="HEX. Порожнє — як зараз на сайті.",
                        max_length=32,
                        verbose_name="Колір шрифту",
                    ),
                ),
                (
                    "accent_color",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="HEX. Порожнє — як зараз на сайті.",
                        max_length=32,
                        verbose_name="Колір підсвітки",
                    ),
                ),
            ],
            options={
                "verbose_name": "Оформлення сторінки",
                "verbose_name_plural": "Оформлення сторінок",
                "ordering": ["page"],
            },
        ),
        migrations.RunPython(seed_page_styles, unseed_page_styles),
    ]
