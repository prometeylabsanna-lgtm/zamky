from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


def link_existing(apps, schema_editor):
    PickerDoor = apps.get_model("pages", "PickerDoor")
    PickerFilter = apps.get_model("pages", "PickerFilter")
    Category = apps.get_model("catalog", "Category")
    Attribute = apps.get_model("catalog", "Attribute")
    for door in PickerDoor.objects.all():
        hints = [
            part.strip()
            for part in (door.match_hints or "").split(",")
            if part.strip()
        ]
        if not hints:
            continue
        query = Q()
        for hint in hints:
            query |= Q(name__icontains=hint)
        cats = list(Category.objects.filter(query))
        if cats:
            door.categories.add(*cats)
    for filt in PickerFilter.objects.filter(attribute__isnull=True):
        if filt.key == "price":
            continue
        attr = Attribute.objects.filter(slug=filt.key).first()
        if attr is not None:
            filt.attribute_id = attr.pk
            filt.save(update_fields=["attribute"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0007_category_home_card"),
        ("pages", "0011_picker_subsections"),
    ]

    operations = [
        migrations.AddField(
            model_name="pickerdoor",
            name="categories",
            field=models.ManyToManyField(
                blank=True,
                related_name="picker_doors",
                to="catalog.category",
                verbose_name="Категорії товарів",
            ),
        ),
        migrations.AddField(
            model_name="pickerfilter",
            name="attribute",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="picker_filters",
                to="catalog.attribute",
                verbose_name="Фільтр каталогу",
            ),
        ),
        migrations.AlterField(
            model_name="pickerfilter",
            name="key",
            field=models.SlugField(max_length=64, unique=True, verbose_name="Ключ"),
        ),
        migrations.RunPython(link_existing, migrations.RunPython.noop),
    ]
