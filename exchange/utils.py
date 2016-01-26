from uuid import uuid4
import re
from decimal import Decimal

from lxml import html

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Min, Max

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


def create_new_user():
    return User.objects.create(username=uuid4().hex[:30])


def set_name_cookie(response, name: str):
    response.set_cookie('name', name, max_age=365*86400)
    return response


def get_best_rates(currency: int, exchanger_offices, buy: bool):
    return Rate.objects.filter(
            rate=Rate.objects.filter(
                exchange_office__in=exchanger_offices, currency=currency, buy=buy).aggregate(val=Max('rate') if buy else Min('rate'))['val'],
            exchange_office__in=exchanger_offices, currency=currency, buy=buy
    )


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
            bank_rates.extend((
                cls.build_rate(rate=Decimal(cells[1].text), exchange_office=exchange_office, currency=Rate.USD, buy=True),
                cls.build_rate(rate=Decimal(cells[2].text), exchange_office=exchange_office, currency=Rate.USD, buy=False),
                cls.build_rate(rate=Decimal(cells[3].text), exchange_office=exchange_office, currency=Rate.EUR, buy=True),
                cls.build_rate(rate=Decimal(cells[4].text), exchange_office=exchange_office, currency=Rate.EUR, buy=False),
                cls.build_rate(rate=Decimal(cells[5].text), exchange_office=exchange_office, currency=Rate.RUB, buy=True),
                cls.build_rate(rate=Decimal(cells[6].text), exchange_office=exchange_office, currency=Rate.RUB, buy=False),
            ))
        Rate.objects.all().delete()
        Rate.objects.bulk_create(bank_rates)

    @classmethod
    def build_rate(cls, rate: Decimal, **keys) -> Rate:
        return Rate(rate=rate, **keys)
