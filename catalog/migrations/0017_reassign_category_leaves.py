from django.db import migrations


def reassign_leaves(apps, schema_editor):
    from catalog.category_tree import resolve_leaf_category
    from catalog.models import Product

    qs = Product.objects.select_related('category').prefetch_related(
        'attributes__attribute'
    )
    for product in qs:
        mech = ''
        for value in product.attributes.all():
            if value.attribute.slug == 'mech':
                mech = value.value
                break
        size_ab = ''
        if product.size_a and product.size_b:
            size_ab = f'{product.size_a}×{product.size_b}'
        leaf = resolve_leaf_category(product.category, mech, size_ab)
        if leaf is not None and leaf.pk != product.category_id:
            product.category_id = leaf.pk
            product.save(update_fields=['category'])


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0016_category_menu_tree'),
    ]

    operations = [
        migrations.RunPython(reassign_leaves, noop),
    ]
