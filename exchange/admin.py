from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from exchange.coordinates_loader import multi_update_coordinates
from exchange.models import Bank, ExchangeOffice, Rate, UserInfo, DynamicSettings


class BankAdmin(admin.ModelAdmin):
    list_display = 'name', 'identifier'


class ExchangeOfficeAdmin(admin.ModelAdmin):
    list_display = 'bank', 'address', 'coordinates', 'identifier', 'is_removed'
    list_filter = 'is_removed', 'no_coordinates', 'bank'
    search_fields = 'bank', 'address', 'identifier'
    actions = 'update_coordinates',

    def update_coordinates(self, request, queryset):
        multi_update_coordinates(queryset)

    def coordinates(self, obj: ExchangeOffice):
        if obj.no_coordinates:
            return '-'

        if obj.latitude is None or obj.longitude is None:
            return _('Undefined')

        return f'{obj.latitude}, {obj.longitude}'

    update_coordinates.short_description = _('Update coordinates')


class RateAdmin(admin.ModelAdmin):
    list_display = 'exchange_office', 'currency', 'buy', 'rate'
    list_filter = 'currency', 'buy', 'exchange_office__bank'


class UserInfoAdmin(admin.ModelAdmin):
    list_display = 'name', 'ip', 'last_changed'
    filter_horizontal = 'exchange_offices',


class DynamicSettingsAdmin(admin.ModelAdmin):
    list_display = 'key', 'value'


admin.site.register(Bank, BankAdmin)
admin.site.register(ExchangeOffice, ExchangeOfficeAdmin)
admin.site.register(Rate, RateAdmin)
admin.site.register(UserInfo, UserInfoAdmin)
admin.site.register(DynamicSettings, DynamicSettingsAdmin)
