from django.db import migrations


def seed_blog_ask(apps, schema_editor):
    SiteBlock = apps.get_model("pages", "SiteBlock")

    def consult(key, fallback):
        row = SiteBlock.objects.filter(page="site", key=key).first()
        text = (getattr(row, "text_html", "") or "").strip() if row else ""
        ru = (getattr(row, "text_html_ru", "") or "").strip() if row else ""
        return text or fallback, ru

    phone, phone_ru = consult("info_consult_phone", "067 00 00 00")
    hours, hours_ru = consult("info_consult_hours", "Пн–Сб, 9:00–19:00")
    rows = (
        ("blog_ask_visible", "Показувати картку", "1", ""),
        ("blog_ask_title", "Заголовок", "Маєте питання?", "Есть вопросы?"),
        (
            "blog_ask_text",
            "Текст",
            "Консультуємо щодня в телефоні, Viber та Telegram",
            "Консультируем ежедневно по телефону, Viber и Telegram",
        ),
        ("blog_ask_phone", "Телефон", phone, phone_ru),
        ("blog_ask_hours", "Графік", hours, hours_ru),
        ("blog_ask_cta", "Текст кнопки", "Замовити дзвінок", "Заказать звонок"),
    )
    for key, label, ua, ru in rows:
        SiteBlock.objects.get_or_create(
            page="blog",
            key=key,
            defaults={
                "label": label,
                "content_type": "text",
                "text_html": ua,
                "text_html_ru": ru,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0019_blog_layout_copy"),
    ]

    operations = [
        migrations.CreateModel(
            name="BlogAskSettings",
            fields=[],
            options={
                "verbose_name": "Маєте питання?",
                "verbose_name_plural": "Маєте питання?",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("pages.sitesettings",),
        ),
        migrations.RunPython(seed_blog_ask, migrations.RunPython.noop),
    ]
