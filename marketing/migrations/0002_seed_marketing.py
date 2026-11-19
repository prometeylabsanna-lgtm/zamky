from django.db import migrations


def forwards(apps, schema_editor):
    from marketing.seed import seed_marketing

    seed_marketing(
        apps.get_model("marketing", "SeoSettings"),
        apps.get_model("marketing", "TrackingSettings"),
        apps.get_model("marketing", "ProductFeed"),
        apps.get_model("pages", "SiteSettings"),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("marketing", "0001_initial"),
        ("pages", "0008_heroslide_cta_buttons"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
