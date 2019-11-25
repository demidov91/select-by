import re
from decimal import Decimal

from django.conf import settings
from django.db.models.functions import Length
from lxml import html

from exchange.constants import DEFAULT_TIMEOUT
from exchange.coordinates_loader import update_all_coordinates
from exchange.models import DynamicSettings, Rate, Bank, ExchangeOffice
from exchange.services import set_dynamic_setting
from exchange.utils.common import BaseLoader
from exchange.utils.dynamic_settings import get_dynamic_setting


import logging
logger = logging.getLogger(__name__)


class SelectbyLoader(BaseLoader):
    bank_identifier_matcher = re.compile('.*/(\d+/\d+)/')
    exchange_office_identifier_matcher = re.compile('.*id(\d+)')

    def __init__(self):
        super(SelectbyLoader, self).__init__()
        self._offices = set()

    def add_office(self, *office_id):
        self._offices.update(office_id)

    def get_expected_exchange_offices(self):
        return ExchangeOffice.objects.annotate(length=Length('identifier')).filter(length__lt=4)

    def _load(self):
        page_doc = self.load_page_source()
        last_update = self.get_last_page_update(page_doc)
        if get_dynamic_setting(DynamicSettings.LAST_UPDATE_KEY) == last_update:
            return False
        set_dynamic_setting(DynamicSettings.LAST_UPDATE_KEY, last_update)
        self.parse_page_data(page_doc)
        return True

    def load(self):
        super().load()
        update_all_coordinates()

    def load_page_source(self):
        return html.fromstring(
            self.client.get(settings.RATES_SOURCE, timeout=DEFAULT_TIMEOUT).content
        )

    def get_last_page_update(self, doc) -> str:
        return doc.cssselect('.kurs_h3')[0].text.strip()

    def parse_page_data(self, doc):
        bank = None
        for row in doc.cssselect('#curr_table tbody tr:not(.static)'):
            classes = row.get('class')
            cells = row.getchildren()
            if not classes or 'tablesorter-childRow' not in classes:
                bank_cells = cells[1].getchildren()
                if bank_cells:
                    identifier = bank_cells[0].get('href')
                    name = bank_cells[0].text.strip()
                else:
                    bank = None
                    continue

                bank = self.get_bank(identifier, name)
                logger.debug('Processing bank {}'.format(bank.name))
                continue

            if len(cells[0].cssselect('a')) == 0:
                continue

            if bank is None:
                logger.error('Unknown bank!')
                continue

            exchange_office = self.get_exchange_office(bank, cells[0].cssselect('a')[0])
            self.add_office(exchange_office.id)
            self.add_rate(
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
            )

    def build_rate(self, rate: Decimal, **keys) -> Rate:
        return Rate(rate=rate, **keys)

    def get_bank(self, identifier: str, name: str) -> Bank:
        try:
            return Bank.objects.get(identifier=identifier)
        except Bank.DoesNotExist:
            logger.info('Bank with identifier {} and name {} will be created.'.format(
                identifier, name))
            return Bank.objects.create(identifier=identifier, name=name)

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