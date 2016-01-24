from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class Bank(models.Model):
    identifier = models.CharField(null=False, max_length=63, unique=True, verbose_name=_('identifier'))
    name = models.CharField(null=False, max_length=63, verbose_name=_('name'))

    def __str__(self):
        return self.name


class ExchangeOffice(models.Model):
    identifier = models.CharField(null=False, max_length=63, unique=True, verbose_name=_('identifier'))
    address = models.CharField(null=False, max_length=127, verbose_name=_('address'))
    bank = models.ForeignKey(Bank, null=False)

    def __str__(self):
        return '{}: {}'.format(self.bank.name, self.address)


class Rate(models.Model):
    USD = 0
    EUR = 1
    RUB = 2

    CURRENCIES = (
        (USD, _('usd')),
        (EUR, _('eur')),
        (RUB, _('rub')),
    )

    exchange_office = models.ForeignKey(ExchangeOffice, null=False)
    currency = models.PositiveSmallIntegerField(null=False, choices=CURRENCIES, verbose_name=_('currency'))
    buy = models.BooleanField(verbose_name=_('buy'))
    rate = models.DecimalField(max_digits=11, decimal_places=4, null=False, verbose_name=_('rate'))

    def __str__(self):
        return '{} {} for {}'.format(_('buy') if self.buy else _('sell'), self.CURRENCIES[self.currency][1], self.exchange_office.bank)


class DynamicSettings(models.Model):
    LAST_UPDATE_KEY = 'last update'

    key = models.CharField(max_length=31, null=False)
    value = models.CharField(max_length=255, null=True)


class UserInfo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, verbose_name=_('user'))
    ip = models.GenericIPAddressField(null=False, verbose_name=_('registration IP address'))
    exchange_offices = models.ManyToManyField(ExchangeOffice)
