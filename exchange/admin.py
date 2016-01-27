from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from exchange.models import Bank, ExchangeOffice, Rate, UserInfo, DynamicSettings


class BankAdmin(admin.ModelAdmin):
    list_display = 'name', 'identifier'


class ExchangeOfficeAdmin(admin.ModelAdmin):
    list_display = 'bank', 'address', 'identifier'


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
