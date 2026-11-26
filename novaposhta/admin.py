from django.contrib import admin
from unfold.admin import ModelAdmin

from pages.admin_mixins import TopDropdownFiltersMixin

from .models import NPCity, NPSyncRun, NPWarehouse


def _all_fields(model):
    return [field.name for field in model._meta.fields]


class _ReadOnlyDirectoryAdmin(TopDropdownFiltersMixin, ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def get_readonly_fields(self, request, obj=None):
        return _all_fields(self.model)


@admin.register(NPWarehouse)
class NPWarehouseAdmin(_ReadOnlyDirectoryAdmin):
    list_display = ('number', 'city_name', 'category', 'short_address', 'is_active')
    list_filter = ('is_active', 'category', 'settlement_area')
    search_fields = ('number', 'city_name', 'description')
    ordering = ('city_name', 'number_int', 'number')
    list_per_page = 50


@admin.register(NPCity)
class NPCityAdmin(_ReadOnlyDirectoryAdmin):
    list_display = ('name', 'area', 'region', 'settlement_type', 'is_active')
    list_filter = ('is_active', 'area', 'settlement_type')
    search_fields = ('name', 'name_ru', 'area', 'region')
    ordering = ('name',)
    list_per_page = 50


@admin.register(NPSyncRun)
class NPSyncRunAdmin(_ReadOnlyDirectoryAdmin):
    list_display = (
        'started_at',
        'status',
        'pages',
        'received',
        'created',
        'updated',
        'deactivated',
    )
    list_filter = ('status',)
    search_fields = ('message',)
    ordering = ('-started_at',)
    list_per_page = 50
