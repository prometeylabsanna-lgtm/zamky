from django.db import migrations, models


def seed_overlay(apps, schema_editor):
    HeroSlide = apps.get_model("pages", "HeroSlide")
    from pages.hero_slides import DEFAULT_HERO_SLIDES, apply_overlay_defaults

    slides = list(HeroSlide.objects.all().order_by("sort_order", "id"))
    for index, slide in enumerate(slides):
        if index >= len(DEFAULT_HERO_SLIDES):
            break
        apply_overlay_defaults(slide, DEFAULT_HERO_SLIDES[index])
        name = (getattr(slide.image, "name", None) or "").lower()
        if "banner" in name or name.endswith("hero.webp") or name.endswith("hero.png"):
            slide.image = ""
        slide.save()


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0008_heroslide_cta_buttons"),
    ]

    operations = [
        migrations.AddField(
            model_name="heroslide",
            name="headline",
            field=models.CharField(
                blank=True, default="", max_length=160, verbose_name="Заголовок (UA)"
            ),
        ),
        migrations.AddField(
            model_name="heroslide",
            name="headline_ru",
            field=models.CharField(
                blank=True, default="", max_length=160, verbose_name="Заголовок (RU)"
            ),
        ),
        migrations.AddField(
            model_name="heroslide",
            name="headline_accent",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Наприклад 24/7 — показується оранжевим після заголовка.",
                max_length=32,
                verbose_name="Акцент у заголовку (UA)",
            ),
        ),
        migrations.AddField(
            model_name="heroslide",
            name="headline_accent_ru",
            field=models.CharField(
                blank=True,
                default="",
                max_length=32,
                verbose_name="Акцент у заголовку (RU)",
            ),
        ),
        migrations.AddField(
            model_name="heroslide",
            name="subtitle",
            field=models.CharField(
                blank=True, default="", max_length=240, verbose_name="Підзаголовок (UA)"
            ),
        ),
        migrations.AddField(
            model_name="heroslide",
            name="subtitle_ru",
            field=models.CharField(
                blank=True, default="", max_length=240, verbose_name="Підзаголовок (RU)"
            ),
        ),
        migrations.AddField(
            model_name="heroslide",
            name="show_secondary",
            field=models.BooleanField(default=False, verbose_name="Друга кнопка"),
        ),
        migrations.AddField(
            model_name="heroslide",
            name="cta_primary_light",
            field=models.BooleanField(
                default=False,
                help_text="Біла кнопка з оранжевим текстом (акції / бренди).",
                verbose_name="Кнопка 1 світла",
            ),
        ),
        migrations.AddField(
            model_name="heroslide",
            name="show_features",
            field=models.BooleanField(
                default=False, verbose_name="Картки переваг справа"
            ),
        ),
        migrations.AddField(
            model_name="heroslide",
            name="show_brands",
            field=models.BooleanField(default=False, verbose_name="Логотипи брендів"),
        ),
        migrations.RunPython(seed_overlay, noop),
    ]
