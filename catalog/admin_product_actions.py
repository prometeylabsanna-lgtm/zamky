"""Масові дії для товарів у адмінці."""

from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.shortcuts import redirect, render
from django.utils.translation import ngettext

from catalog.models import Category


@admin.action(description='Активувати')
def make_active(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        ngettext('%(c)d товар активовано.', '%(c)d товарів активовано.', updated)
        % {'c': updated},
        messages.SUCCESS,
    )


@admin.action(description='Деактивувати')
def make_inactive(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        ngettext('%(c)d товар деактивовано.', '%(c)d товарів деактивовано.', updated)
        % {'c': updated},
        messages.SUCCESS,
    )


@admin.action(description='Хіт — так')
def make_hit(modeladmin, request, queryset):
    updated = queryset.update(is_hit=True)
    modeladmin.message_user(
        request,
        ngettext('%(c)d товар позначено хітом.', '%(c)d товарів позначено хітами.', updated)
        % {'c': updated},
        messages.SUCCESS,
    )


@admin.action(description='Хіт — ні')
def unmake_hit(modeladmin, request, queryset):
    updated = queryset.update(is_hit=False)
    modeladmin.message_user(
        request,
        ngettext('%(c)d товар: знято хіт.', '%(c)d товарів: знято хіт.', updated)
        % {'c': updated},
        messages.SUCCESS,
    )


@admin.action(description='Новинка — так')
def make_new(modeladmin, request, queryset):
    updated = queryset.update(is_new=True)
    modeladmin.message_user(
        request,
        ngettext('%(c)d товар позначено новинкою.', '%(c)d товарів позначено новинками.', updated)
        % {'c': updated},
        messages.SUCCESS,
    )


@admin.action(description='Новинка — ні')
def unmake_new(modeladmin, request, queryset):
    updated = queryset.update(is_new=False)
    modeladmin.message_user(
        request,
        ngettext('%(c)d товар: знято новинку.', '%(c)d товарів: знято новинку.', updated)
        % {'c': updated},
        messages.SUCCESS,
    )


@admin.action(description='Змінити категорію')
def change_category(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    selected = request.POST.getlist(ACTION_CHECKBOX_NAME)

    if 'apply' in request.POST:
        category_id = request.POST.get('category')
        if not category_id:
            modeladmin.message_user(request, 'Оберіть категорію.', messages.ERROR)
        else:
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                modeladmin.message_user(request, 'Категорію не знайдено.', messages.ERROR)
            else:
                updated = queryset.update(category=category)
                modeladmin.message_user(
                    request,
                    ngettext(
                        '%(c)d товар перенесено до «%(name)s».',
                        '%(c)d товарів перенесено до «%(name)s».',
                        updated,
                    )
                    % {'c': updated, 'name': category.name},
                    messages.SUCCESS,
                )
        return redirect(f'admin:{opts.app_label}_{opts.model_name}_changelist')

    context = {
        **modeladmin.admin_site.each_context(request),
        'title': 'Змінити категорію',
        'queryset': queryset,
        'opts': opts,
        'action_checkbox_name': ACTION_CHECKBOX_NAME,
        'selected': selected,
        'categories': Category.objects.order_by('sort_order', 'name'),
        'media': modeladmin.media,
    }
    return render(request, 'admin/catalog/change_category.html', context)


PRODUCT_ACTIONS = [
    make_active,
    make_inactive,
    make_hit,
    unmake_hit,
    make_new,
    unmake_new,
    change_category,
    'delete_selected',
]
