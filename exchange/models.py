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
    bank = models.ForeignKey(Bank, null=False, on_delete=models.CASCADE)
    latitude = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('latitude')
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('longitude')
    )
    no_coordinates = models.BooleanField(default=False, verbose_name=_('no coordinates'))

    is_removed = models.BooleanField(default=False, verbose_name=_('is removed'))

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

    exchange_office = models.ForeignKey(ExchangeOffice, null=False, on_delete=models.CASCADE)
    currency = models.PositiveSmallIntegerField(null=False, choices=CURRENCIES, verbose_name=_('currency'))
    buy = models.BooleanField(verbose_name=_('buy'))
    rate = models.DecimalField(max_digits=11, decimal_places=4, null=False, verbose_name=_('rate'))

    def __str__(self):
        return '{} {} for {}'.format(
            _('buy') if self.buy else _('sell'),
            self.CURRENCIES[self.currency][1], self.exchange_office.bank
        )


class DynamicSettings(models.Model):
    LAST_UPDATE_KEY = 'last update'
    NBRB_RATES_DATE = 'nbrb rates date'
    NBRB_USD = 'nbrb usd'
    NBRB_EUR = 'nbrb eur'
    NBRB_RUB = 'nbrb rub'

    key = models.CharField(max_length=31, null=False)
    value = models.CharField(max_length=255, null=True)


class UserInfo(models.Model):
    name = models.CharField(max_length=127, null=True, unique=True, verbose_name=_('name'))
    ip = models.GenericIPAddressField(null=False, verbose_name=_('registration IP address'))
    exchange_offices = models.ManyToManyField(ExchangeOffice)
    last_changed = models.DateTimeField(auto_now=True, null=False, verbose_name=_('last changed'))
