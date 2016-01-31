import base64
import re
from decimal import Decimal
from contextlib import contextmanager

from lxml import html

from django.conf import settings
from django.db.models import Min, Max, Q
from django.db.transaction import atomic
from django.db import connection

from exchange.models import DynamicSettings, Bank, Rate, ExchangeOffice

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
    '19': DynamicSettings.NBRB_EUR,
    '190': DynamicSettings.NBRB_RUB,
}


@contextmanager
def lock_table(table_name):
    with connection.cursor() as cursor:
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
            with atomic:
                logger.debug('Table will be locked now')
                cursor.execute('lock table %s nowait', table_name)
                logger.debug('Table is locked')
                yield
                logger.debug('Doing nothing to release the table')
        else:
            logger.warning('Unknown db table should be locked...')
            yield
            logger.warning('Unknown db table lock should be released...')


class RatesLoader:
    bank_identifier_matcher = re.compile('.*/(\d+/\d+)/')
    exchange_office_identifier_matcher = re.compile('.*id(\d+)')

    @classmethod
    def load(cls):
        page_doc = cls.load_page_source()
        last_update = cls.get_last_page_update(page_doc)
        if get_dynamic_setting(DynamicSettings.LAST_UPDATE_KEY) == last_update:
            logger.info('Nothing has changed')
            return
        set_dynamic_setting(DynamicSettings.LAST_UPDATE_KEY, last_update)
        cls.save_page_data(page_doc)

    @classmethod
    def load_page_source(cls):
        return html.parse(settings.RATES_SOURCE).getroot()

    @classmethod
    def get_last_page_update(cls, doc) -> str:
        return doc.cssselect('.kurs_h3')[0].text.strip()

    @classmethod
    def get_bank(cls, link) -> Bank:
        try:
            return Bank.objects.get(identifier=link.get('href'))
        except Bank.DoesNotExist:
            logger.info('Bank with identifier {} and name {} will be created.'.format(
                link.get('href'), link.text.strip()))
            return Bank.objects.get_or_create(identifier=link.get('href'), name=link.text.strip())[0]

    @classmethod
    def get_exchange_office(cls, bank: Bank, link) -> ExchangeOffice:
        match = cls.exchange_office_identifier_matcher.match(link.get('href'))
        if not match:
            raise ValueError('{} is illegal bank link'.format(link.get('href')))
        try:
            return ExchangeOffice.objects.get(identifier=match.group(1))
        except ExchangeOffice.DoesNotExist:
            logger.info('Exchange office with identifier {} and address {} will be created for bank {}.'.format(
                match.group(1), link.text.strip(), bank.name))
            return ExchangeOffice.objects.get_or_create(bank=bank, identifier=match.group(1), address=link.text.strip())[0]

    @classmethod
    def save_page_data(cls, doc):
        bank = None
        bank_rates = []
        fresh_offices = set()
        for row in doc.cssselect('#curr_table tbody tr:not(.static)'):
            classes = row.get('class')
            cells = row.getchildren()
            if not classes or 'tablesorter-childRow' not in classes:
                bank = cls.get_bank(next(cells[1].iterchildren()))
                logger.debug('Processing bank {}'.format(bank.name))
                continue
            if bank is None:
                logger.error('Unknown bank!')
                continue
            exchange_office = cls.get_exchange_office(bank, cells[0].cssselect('a')[0])
            fresh_offices.add(exchange_office.id)
            bank_rates.extend((
                cls.build_rate(rate=Decimal(cells[1].text), exchange_office=exchange_office, currency=Rate.USD, buy=True),
                cls.build_rate(rate=Decimal(cells[2].text), exchange_office=exchange_office, currency=Rate.USD, buy=False),
                cls.build_rate(rate=Decimal(cells[3].text), exchange_office=exchange_office, currency=Rate.EUR, buy=True),
                cls.build_rate(rate=Decimal(cells[4].text), exchange_office=exchange_office, currency=Rate.EUR, buy=False),
                cls.build_rate(rate=Decimal(cells[5].text), exchange_office=exchange_office, currency=Rate.RUB, buy=True),
                cls.build_rate(rate=Decimal(cells[6].text), exchange_office=exchange_office, currency=Rate.RUB, buy=False),
            ))
        with lock_table(Rate._meta.db_table):
            Rate.objects.all().delete()
            Rate.objects.bulk_create(bank_rates)
        ExchangeOffice.objects.filter(~Q(id__in=fresh_offices)).delete()

    @classmethod
    def build_rate(cls, rate: Decimal, **keys) -> Rate:
        return Rate(rate=rate, **keys)


@atomic
def save_rates(doc):
    set_dynamic_setting(DynamicSettings.NBRB_RATES_DATE, doc.get('Date'))
    for rate in filter(lambda x: x.get('Id') in CURRENCY_TO_DYNAMIC_SETTING.keys(), doc):
        value = None
        for field in rate:
            if field.tag == 'Rate':
                value = field.text
        if value is None:
            logger.error('Broken rate!')
            raise ValueError('Broken {} rate.'.format(rate.get('Id')))
        set_dynamic_setting(CURRENCY_TO_DYNAMIC_SETTING[rate.get('Id')], value)
