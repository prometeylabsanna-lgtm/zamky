from django.db.models import Max


def next_sort_order(qs, exclude_pk=None):
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    current = qs.aggregate(m=Max('sort_order'))['m']
    if not current:
        return 1
    return int(current) + 1


def apply_auto_sort_order(instance, sibling_qs):
    if instance.sort_order:
        return
    instance.sort_order = next_sort_order(sibling_qs, exclude_pk=instance.pk)


def fill_zero_sort_orders(qs, name_field):
    items = list(qs.order_by('sort_order', name_field, 'pk'))
    used = {obj.sort_order for obj in items if obj.sort_order}
    nxt = 1
    changed = []
    for obj in items:
        if obj.sort_order:
            continue
        while nxt in used:
            nxt += 1
        obj.sort_order = nxt
        used.add(nxt)
        nxt += 1
        changed.append(obj)
    if changed:
        qs.model.objects.bulk_update(changed, ['sort_order'])
    return len(changed)


def normalize_sort_from_one(qs, name_field):
    items = list(qs.order_by('sort_order', name_field, 'pk'))
    if not items or all(obj.sort_order for obj in items):
        return 0
    orders = [obj.sort_order for obj in items]
    unique = sorted(set(orders))
    if unique == list(range(len(unique))) and len(unique) == len(items):
        for obj in items:
            obj.sort_order += 1
        qs.model.objects.bulk_update(items, ['sort_order'])
        return len(items)
    return fill_zero_sort_orders(qs, name_field)
