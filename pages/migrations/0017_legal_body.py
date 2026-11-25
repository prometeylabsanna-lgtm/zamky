from django.db import migrations


def _values(SiteBlock, page: str, keys: tuple[str, ...], ru: bool) -> dict[str, str]:
    field = "text_html_ru" if ru else "text_html"
    rows = SiteBlock.objects.filter(page=page, key__in=keys)
    return {row.key: getattr(row, field, "") or "" for row in rows}


def forwards(apps, schema_editor):
    SiteBlock = apps.get_model("pages", "SiteBlock")
    from pages.block_defaults import get_block_content_type, get_block_label
    from pages.legal_body import (
        OFFER_OLD_KEYS,
        PRIVACY_OLD_KEYS,
        compose_offer_from_values,
        compose_privacy_from_values,
        default_offer_html,
        default_privacy_html,
        is_html_body,
    )

    specs = (
        (
            "offer",
            "offer_body",
            OFFER_OLD_KEYS,
            compose_offer_from_values,
            default_offer_html,
        ),
        (
            "privacy",
            "privacy_body",
            PRIVACY_OLD_KEYS,
            compose_privacy_from_values,
            default_privacy_html,
        ),
    )
    for page, key, old_keys, compose, default_html in specs:
        ua_src = _values(SiteBlock, page, old_keys, ru=False)
        ru_src = _values(SiteBlock, page, old_keys, ru=True)
        ua_html = compose(ua_src) if any(ua_src.values()) else default_html("ua")
        ru_html = compose(ru_src) if any(ru_src.values()) else default_html("ru")
        defaults = {
            "label": get_block_label(page, key),
            "content_type": get_block_content_type(page, key),
            "text_html": ua_html,
            "text_html_ru": ru_html,
            "is_active": True,
        }
        block, created = SiteBlock.objects.get_or_create(
            page=page, key=key, defaults=defaults
        )
        if not created:
            dirty = False
            if not is_html_body(block.text_html or ""):
                block.text_html = ua_html
                dirty = True
            if not is_html_body(block.text_html_ru or "") and ru_html:
                block.text_html_ru = ru_html
                dirty = True
            if dirty:
                block.save(update_fields=["text_html", "text_html_ru"])
        SiteBlock.objects.filter(page=page, key__in=old_keys).delete()


def backwards(apps, schema_editor):
    SiteBlock = apps.get_model("pages", "SiteBlock")
    SiteBlock.objects.filter(
        page__in=("offer", "privacy"), key__in=("offer_body", "privacy_body")
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0016_about_form_settings"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
