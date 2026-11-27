from django.db import migrations

DOMAIN = "https://centerzamkiv.com.ua"


def set_primary_domain(apps, schema_editor):
    SeoSettings = apps.get_model("marketing", "SeoSettings")
    row = SeoSettings.objects.order_by("pk").first()
    if row is None:
        SeoSettings.objects.create(primary_domain=DOMAIN)
        return
    if not (row.primary_domain or "").strip():
        row.primary_domain = DOMAIN
        row.save(update_fields=["primary_domain"])


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0003_productfeed_last_warnings"),
    ]

    operations = [
        migrations.RunPython(set_primary_domain, migrations.RunPython.noop),
    ]
