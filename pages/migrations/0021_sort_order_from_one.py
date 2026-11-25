from django.db import migrations


def fill_pages_sort(apps, schema_editor):
    from catalog.filter_sort import normalize_sort_from_one

    BlogPost = apps.get_model('pages', 'BlogPost')
    HeaderNavLink = apps.get_model('pages', 'HeaderNavLink')
    FooterNavLink = apps.get_model('pages', 'FooterNavLink')
    HomePopularProduct = apps.get_model('pages', 'HomePopularProduct')
    PickerDoor = apps.get_model('pages', 'PickerDoor')
    PickerFilter = apps.get_model('pages', 'PickerFilter')
    PickerFilterOption = apps.get_model('pages', 'PickerFilterOption')
    HeroSlide = apps.get_model('pages', 'HeroSlide')

    normalize_sort_from_one(BlogPost.objects.all(), 'title')
    normalize_sort_from_one(HeaderNavLink.objects.all(), 'name')
    normalize_sort_from_one(HeroSlide.objects.all(), 'pk')
    normalize_sort_from_one(PickerDoor.objects.all(), 'code')
    normalize_sort_from_one(PickerFilter.objects.all(), 'key')
    for group in FooterNavLink.objects.values_list('group', flat=True).distinct():
        normalize_sort_from_one(FooterNavLink.objects.filter(group=group), 'name')
    for tab in HomePopularProduct.objects.values_list('tab', flat=True).distinct():
        normalize_sort_from_one(HomePopularProduct.objects.filter(tab=tab), 'pk')
    for filt_id in PickerFilterOption.objects.values_list(
        'filter_id', flat=True
    ).distinct():
        normalize_sort_from_one(
            PickerFilterOption.objects.filter(filter_id=filt_id), 'label'
        )


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0020_blog_ask_settings'),
    ]

    operations = [
        migrations.RunPython(fill_pages_sort, noop),
    ]
