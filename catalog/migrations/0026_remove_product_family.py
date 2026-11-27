from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0025_review_active_counter'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='family',
        ),
        migrations.DeleteModel(
            name='FamilyColorSwatch',
        ),
        migrations.DeleteModel(
            name='ProductFamily',
        ),
    ]
