from django.db import migrations, models


def show_info_in_mobile(apps, schema_editor):
    Link = apps.get_model("pages", "HeaderNavLink")
    Link.objects.filter(key__in=["promos", "install"]).update(in_mobile=True)


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0023_cartchromesettings_catalogsortsettings_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="headernavlink",
            name="in_header",
            field=models.BooleanField(default=True, verbose_name="Під пошуком"),
        ),
        migrations.AddField(
            model_name="headernavlink",
            name="in_mobile",
            field=models.BooleanField(default=False, verbose_name="У меню телефону"),
        ),
        migrations.RunPython(show_info_in_mobile, migrations.RunPython.noop),
    ]
