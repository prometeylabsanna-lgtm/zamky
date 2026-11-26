"""Повний прохід getWarehouses: upsert відділень, потім деактивація зниклих."""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from config.cache_safe import cache_delete
from novaposhta.client import NPApiError, NovaPoshtaClient
from novaposhta.models import NPCity, NPSyncRun, NPWarehouse
from novaposhta.normalize import city_search_norm, warehouse_search_norm

# Той самий ключ, що в novaposhta.search.has_data.
_HAS_DATA_KEY = 'novaposhta.has_data'

logger = logging.getLogger(__name__)

_WH_UPDATE = [
    'number',
    'number_int',
    'category',
    'type_ref',
    'description',
    'description_ru',
    'short_address',
    'short_address_ru',
    'city_ref',
    'city_name',
    'city_name_ru',
    'settlement_area',
    'settlement_region',
    'max_weight',
    'is_active',
    'is_selectable',
    'search_norm',
    'updated_at',
    'last_seen_sync',
]
_CITY_UPDATE = [
    'name',
    'name_ru',
    'area',
    'region',
    'settlement_type',
    'is_active',
    'search_norm',
    'updated_at',
]
_RUN_FIELDS = [
    'finished_at',
    'status',
    'pages',
    'received',
    'created',
    'updated',
    'deactivated',
    'message',
]


def sync_warehouses(client=None, limit=500, max_pages=400):
    limit = int(limit or 500)
    max_pages = int(max_pages or 400)
    if limit < 1:
        limit = 500
    if max_pages < 1:
        max_pages = 1

    run, owned = _acquire_run()
    if not owned:
        return run

    pages = 0
    received = 0
    created = 0
    updated = 0
    seen_refs = set()
    city_acc = {}
    try:
        if client is None:
            client = NovaPoshtaClient()
        page = 1
        finished = False
        while page <= max_pages:
            payload = client.get_warehouses(page, limit)
            rows = _rows(payload)
            total = _total(payload)
            if not rows:
                finished = True
                break
            page_created, page_updated = _upsert_warehouses(rows, run, seen_refs, city_acc)
            created += page_created
            updated += page_updated
            pages += 1
            received += len(rows)
            if total and page * limit >= total:
                finished = True
                break
            page += 1
        if not finished:
            _save_run(
                run,
                NPSyncRun.Status.FAILED,
                pages,
                received,
                created,
                updated,
                0,
                'Досягнуто ліміт сторінок до кінця довідника. Нічого не деактивовано.',
            )
            return run
        deactivated = _finalize(run, city_acc)
        _save_run(
            run,
            NPSyncRun.Status.SUCCESS,
            pages,
            received,
            created,
            updated,
            deactivated,
            (
                f'Отримано {received}, створено {created}, оновлено {updated}, '
                f'деактивовано {deactivated}.'
            ),
        )
        return run
    except Exception as exc:
        logger.warning('np sync failed: %s', type(exc).__name__)
        _save_run(
            run,
            NPSyncRun.Status.FAILED,
            pages,
            received,
            created,
            updated,
            0,
            _safe_message(exc),
        )
        return run
    finally:
        cache_delete(_HAS_DATA_KEY)


def _acquire_run():
    cutoff = timezone.now() - timedelta(hours=2)
    with transaction.atomic():
        NPSyncRun.objects.filter(
            status=NPSyncRun.Status.RUNNING,
            started_at__lt=cutoff,
        ).update(
            status=NPSyncRun.Status.FAILED,
            finished_at=timezone.now(),
            message='Перервано: попередня синхронізація не завершилась за 2 години.',
        )
        current = (
            NPSyncRun.objects.select_for_update()
            .filter(status=NPSyncRun.Status.RUNNING, started_at__gte=cutoff)
            .order_by('-started_at')
            .first()
        )
        if current:
            return current, False
        run = NPSyncRun.objects.create(status=NPSyncRun.Status.RUNNING, message='')
        return run, True


def _rows(payload):
    if not isinstance(payload, dict):
        raise NPApiError('Некоректна відповідь API Нової пошти')
    data = payload.get('data')
    if data is None:
        return []
    if not isinstance(data, list):
        raise NPApiError('Некоректна відповідь API Нової пошти')
    deduped = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        ref = str(row.get('Ref') or '').strip()
        if ref:
            deduped[ref[:36]] = row
    return list(deduped.values())


def _total(payload) -> int:
    info = payload.get('info') if isinstance(payload, dict) else None
    raw = (info or {}).get('totalCount') if isinstance(info, dict) else 0
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _upsert_warehouses(rows, run, seen_refs, city_acc):
    now = timezone.now()
    objects = []
    refs = []
    for row in rows:
        obj = _warehouse_from_row(row, run, now)
        if obj is None:
            continue
        objects.append(obj)
        refs.append(obj.ref)
        _remember_city(city_acc, row)
    if not objects:
        return 0, 0
    existing = set(NPWarehouse.objects.filter(ref__in=refs).values_list('ref', flat=True))
    created = 0
    updated = 0
    for ref in refs:
        if ref in existing or ref in seen_refs:
            updated += 1
        else:
            created += 1
        seen_refs.add(ref)
    with transaction.atomic():
        for offset in range(0, len(objects), 500):
            NPWarehouse.objects.bulk_create(
                objects[offset : offset + 500],
                update_conflicts=True,
                unique_fields=['ref'],
                update_fields=_WH_UPDATE,
            )
    return created, updated


def _finalize(run, city_acc) -> int:
    with transaction.atomic():
        deactivated = NPWarehouse.objects.exclude(last_seen_sync_id=run.pk).update(is_active=False)
        active_cities = set(
            NPWarehouse.objects.filter(is_active=True)
            .exclude(city_ref='')
            .values_list('city_ref', flat=True)
        )
        now = timezone.now()
        NPCity.objects.update(is_active=False)
        cities = []
        for ref, data in city_acc.items():
            cities.append(
                NPCity(
                    ref=ref,
                    name=(data.get('name') or '')[:255],
                    name_ru=(data.get('name_ru') or '')[:255],
                    area=(data.get('area') or '')[:255],
                    region=(data.get('region') or '')[:255],
                    settlement_type=(data.get('settlement_type') or '')[:64],
                    is_active=ref in active_cities,
                    search_norm=city_search_norm(
                        data.get('name'),
                        data.get('name_ru'),
                        data.get('area'),
                        data.get('region'),
                    ),
                    updated_at=now,
                )
            )
        for offset in range(0, len(cities), 500):
            NPCity.objects.bulk_create(
                cities[offset : offset + 500],
                update_conflicts=True,
                unique_fields=['ref'],
                update_fields=_CITY_UPDATE,
            )
        return int(deactivated or 0)


def _remember_city(city_acc, row):
    ref = str(row.get('CityRef') or '').strip()[:36]
    if not ref:
        return
    city_acc[ref] = {
        'name': str(row.get('CityDescription') or '').strip(),
        'name_ru': str(row.get('CityDescriptionRu') or '').strip(),
        'area': str(row.get('SettlementAreaDescription') or '').strip(),
        'region': str(row.get('SettlementRegionsDescription') or '').strip(),
        'settlement_type': str(row.get('SettlementTypeDescription') or '').strip(),
    }


def _warehouse_from_row(row, run, now):
    ref = str(row.get('Ref') or '').strip()[:36]
    if not ref:
        return None
    number = str(row.get('Number') or '').strip()[:16]
    description = str(row.get('Description') or '').strip()
    description_ru = str(row.get('DescriptionRu') or '').strip()
    short_address = str(row.get('ShortAddress') or '').strip()
    short_address_ru = str(row.get('ShortAddressRu') or '').strip()
    city_name = str(row.get('CityDescription') or '').strip()
    city_name_ru = str(row.get('CityDescriptionRu') or '').strip()
    return NPWarehouse(
        ref=ref,
        number=number,
        number_int=_number_int(number),
        category=str(row.get('CategoryOfWarehouse') or '').strip()[:32],
        type_ref=str(row.get('TypeOfWarehouse') or '').strip()[:36],
        description=description[:500],
        description_ru=description_ru[:500],
        short_address=short_address[:300],
        short_address_ru=short_address_ru[:300],
        city_ref=str(row.get('CityRef') or '').strip()[:36],
        city_name=city_name[:255],
        city_name_ru=city_name_ru[:255],
        settlement_area=str(row.get('SettlementAreaDescription') or '').strip()[:255],
        settlement_region=str(row.get('SettlementRegionsDescription') or '').strip()[:255],
        max_weight=_weight(row),
        is_active=str(row.get('WarehouseStatus') or '') == 'Working',
        is_selectable=str(row.get('DenyToSelect') or '0') != '1',
        search_norm=warehouse_search_norm(
            number,
            description,
            description_ru,
            short_address,
            short_address_ru,
            city_name,
            city_name_ru,
        ),
        updated_at=now,
        last_seen_sync_id=run.pk,
    )


def _number_int(number):
    digits = ''.join(char for char in str(number or '') if char.isdigit())
    if not digits:
        return None
    try:
        value = int(digits)
    except ValueError:
        return None
    if value > 2147483647:
        return None
    return value


def _weight(row):
    raw = row.get('TotalMaxWeightAllowed')
    if raw in (None, ''):
        raw = row.get('PlaceMaxWeightAllowed')
    if raw in (None, ''):
        return None
    try:
        value = Decimal(str(raw).replace(',', '.'))
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite():
        return None
    value = value.quantize(Decimal('0.01'))
    if abs(value) >= Decimal('1000000'):
        return None
    return value


def _save_run(run, status, pages, received, created, updated, deactivated, message):
    run.status = status
    run.finished_at = timezone.now()
    run.pages = pages
    run.received = received
    run.created = created
    run.updated = updated
    run.deactivated = deactivated
    run.message = (message or '')[:4000]
    run.save(update_fields=_RUN_FIELDS)


def _safe_message(exc) -> str:
    if isinstance(exc, NPApiError):
        text = str(exc).strip() or 'Помилка API Нової пошти'
    elif isinstance(exc, (TimeoutError, OSError)):
        text = 'Немає зʼєднання з API Нової пошти'
    else:
        text = 'Синхронізація перервана через помилку.'
    from django.conf import settings

    key = getattr(settings, 'NOVA_POSHTA_API_KEY', '') or ''
    if key and key in text:
        text = text.replace(key, '')
    return text[:1000]
