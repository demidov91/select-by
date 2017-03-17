import base64
import re
from decimal import Decimal
import requests
import json

from lxml import html

from django.conf import settings
from django.db.models import Min, Max, Q
from django.db.transaction import atomic
from django.template.defaulttags import register

from exchange.models import DynamicSettings, Bank, Rate, ExchangeOffice
from exchange.mtbank import MtbankLoader

import logging
logger = logging.getLogger(__name__)


def set_or_create(model_class, keys: dict, values: dict):
    if model_class.objects.filter(**keys).exists():
        model_class.objects.filter(**keys).update(**values)
    else:
        keys.update(values)
        model_class.objects.create(**keys)


def get_dynamic_setting(key: str) -> str:
    try:
        return DynamicSettings.objects.get(key=key).value
    except DynamicSettings.DoesNotExist:
        return None


def set_dynamic_setting(key: str, value: str):
    set_or_create(DynamicSettings, {'key': key}, {'value': value})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def get_username(request):
    try:
        return request.GET.get('name',
                               request.COOKIES.get('name') and base64.b64decode(request.COOKIES.get('name')).decode('utf-8'))
    except UnicodeDecodeError:
        return request.COOKIES.get('name')


def set_name_cookie(response, name: str):
    if name:
        response.set_cookie('name', base64.b64encode(name.encode()).decode('ascii'), max_age=365*86400)
    return response


def get_best_rates(currency: int, exchanger_offices, buy: bool):
    return Rate.objects.filter(
            rate=Rate.objects.filter(
                exchange_office__in=exchanger_offices, currency=currency, buy=buy).aggregate(val=Max('rate') if buy else Min('rate'))['val'],
            exchange_office__in=exchanger_offices, currency=currency, buy=buy
    )


CURRENCY_TO_DYNAMIC_SETTING = {
    '145': DynamicSettings.NBRB_USD,
    '292': DynamicSettings.NBRB_EUR,
    '298': DynamicSettings.NBRB_RUB,
}


class RatesLoader:
    bank_identifier_matcher = re.compile('.*/(\d+/\d+)/')
    exchange_office_identifier_matcher = re.compile('.*id(\d+)')

    def __init__(self):
        self.bank_rates = []
        self.fresh_offices = set()

    def _load_select_by(self):
        page_doc = self.load_page_source()
        last_update = self.get_last_page_update(page_doc)
        if get_dynamic_setting(DynamicSettings.LAST_UPDATE_KEY) == last_update:
            return False
        set_dynamic_setting(DynamicSettings.LAST_UPDATE_KEY, last_update)
        self.parse_page_data(page_doc)
        return True

    def _load_mtbank(self):
        loader = MtbankLoader()
        loader.load()
        self.fresh_offices.update(loader.get_offices())
        self.bank_rates.extend(loader.get_rates())

    def _save(self):
        Rate.objects.filter(exchange_office__in=self.fresh_offices).delete()
        Rate.objects.bulk_create(self.bank_rates)
        ExchangeOffice.objects.filter(~Q(id__in=self.fresh_offices)).update(is_removed=True)
        ExchangeOffice.objects.filter(id__in=self.fresh_offices).update(is_removed=False)

    @atomic
    def load(self):
        if not self._load_select_by():
            logger.info('Nothing has changed')
            return False
        self._load_mtbank()
        self._save()
        return True

    def load_page_source(self):
        return html.parse(settings.RATES_SOURCE).getroot()

    def get_last_page_update(self, doc) -> str:
        return doc.cssselect('.kurs_h3')[0].text.strip()

    def get_bank(self, link) -> Bank:
        try:
            return Bank.objects.get(identifier=link.get('href'))
        except Bank.DoesNotExist:
            logger.info('Bank with identifier {} and name {} will be created.'.format(
                link.get('href'), link.text.strip()))
            return Bank.objects.create(identifier=link.get('href'), name=link.text.strip())

    def get_exchange_office(self, bank: Bank, link) -> ExchangeOffice:
        match = self.exchange_office_identifier_matcher.match(link.get('href'))
        if not match:
            raise ValueError('{} is illegal bank link'.format(link.get('href')))
        try:
            return ExchangeOffice.objects.get(identifier=match.group(1))
        except ExchangeOffice.DoesNotExist:
            logger.info('Exchange office with identifier {} and address {} will be created for bank {}.'.format(
                match.group(1), link.text.strip(), bank.name))
            return ExchangeOffice.objects.create(bank=bank, identifier=match.group(1), address=link.text.strip())

    def parse_page_data(self, doc):
        bank = None
        for row in doc.cssselect('#curr_table tbody tr:not(.static)'):
            classes = row.get('class')
            cells = row.getchildren()
            if not classes or 'tablesorter-childRow' not in classes:
                bank = self.get_bank(next(cells[1].iterchildren()))
                logger.debug('Processing bank {}'.format(bank.name))
                continue
            if bank is None:
                logger.error('Unknown bank!')
                continue
            exchange_office = self.get_exchange_office(bank, cells[0].cssselect('a')[0])
            self.fresh_offices.add(exchange_office.id)
            self.bank_rates.extend((
                self.build_rate(rate=Decimal(cells[1].text.replace(',', '.')),
                               exchange_office=exchange_office, currency=Rate.USD, buy=True),
                self.build_rate(rate=Decimal(cells[2].text.replace(',', '.')),
                               exchange_office=exchange_office, currency=Rate.USD, buy=False),
                self.build_rate(rate=Decimal(cells[3].text.replace(',', '.')),
                               exchange_office=exchange_office, currency=Rate.EUR, buy=True),
                self.build_rate(rate=Decimal(cells[4].text.replace(',', '.')),
                               exchange_office=exchange_office, currency=Rate.EUR, buy=False),
                self.build_rate(rate=Decimal(cells[5].text.replace(',', '.')),
                               exchange_office=exchange_office, currency=Rate.RUB, buy=True),
                self.build_rate(rate=Decimal(cells[6].text.replace(',', '.')),
                               exchange_office=exchange_office, currency=Rate.RUB, buy=False),
            ))

    def build_rate(self, rate: Decimal, **keys) -> Rate:
        return Rate(rate=rate, **keys)


@atomic
def save_rates(doc):
    set_dynamic_setting(DynamicSettings.NBRB_RATES_DATE, doc.get('Date'))
    for rate in filter(lambda x: x.get('Id') in CURRENCY_TO_DYNAMIC_SETTING.keys(), doc):
        value = scale = None
        for field in rate:
            if field.tag == 'Rate':
                value = Decimal(field.text)
            elif field.tag == 'Scale':
                scale = int(field.text)
        if (value or scale) is None:
            logger.error('Broken rate!')
            raise ValueError('Broken {} rate.'.format(rate.get('Id')))
        set_dynamic_setting(CURRENCY_TO_DYNAMIC_SETTING[rate.get('Id')], value/scale)


@register.filter
def get_item(dictionary, key):
    """
    Just don't wont to create separate package for one template filter...
    """
    return dictionary.get(key)
