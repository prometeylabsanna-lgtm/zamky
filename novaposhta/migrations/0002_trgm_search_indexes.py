from django.db import migrations

_INDEXES = (
    (
        'np_wh_search_norm_trgm',
        'novaposhta_npwarehouse',
    ),
    (
        'np_city_search_norm_trgm',
        'novaposhta_npcity',
    ),
)


def create_trgm(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
    for name, table in _INDEXES:
        schema_editor.execute(
            f'CREATE INDEX IF NOT EXISTS {name} ON {table} USING gin (search_norm gin_trgm_ops)'
        )


def drop_trgm(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    for name, _table in _INDEXES:
        schema_editor.execute(f'DROP INDEX IF EXISTS {name}')


class Migration(migrations.Migration):

    dependencies = [
        ('novaposhta', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_trgm, drop_trgm),
    ]
