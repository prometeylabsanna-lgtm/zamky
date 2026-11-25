from django.db import migrations, models


def copy_cms_title(apps, schema_editor):
    SiteBlock = apps.get_model("pages", "SiteBlock")
    DeliveryDistrict = apps.get_model("orders", "DeliveryDistrict")
    ua = "Інші райони Києва"
    ru = "Другие районы Киева"
    block = SiteBlock.objects.filter(page="home", key="district_others_title").first()
    if block:
        if (block.text_html or "").strip():
            ua = block.text_html.strip()
        if (block.text_html_ru or "").strip():
            ru = block.text_html_ru.strip()
    DeliveryDistrict.objects.all().update(others_title=ua, others_title_ru=ru)


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_uk_labels_and_timestamps"),
        ("pages", "0015_home_popular_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliverydistrict",
            name="others_title",
            field=models.CharField(
                default="Інші райони Києва",
                help_text="Напис над списком інших районів на сторінці цього району.",
                max_length=200,
                verbose_name="Заголовок інших районів",
            ),
        ),
        migrations.AddField(
            model_name="deliverydistrict",
            name="others_title_ru",
            field=models.CharField(
                blank=True,
                default="Другие районы Киева",
                max_length=200,
                verbose_name="Заголовок інших районів (RU)",
            ),
        ),
        migrations.RunPython(copy_cms_title, migrations.RunPython.noop),
    ]
