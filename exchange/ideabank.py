import datetime
from json.decoder import JSONDecodeError
from typing import Optional, Dict

from exchange.constants import IDEABANK_ONLINE_OFFICE, DEFAULT_TIMEOUT
from exchange.utils.common import BaseLoader
from .defines import (
    IDEABANK_URL,
    IDEABANK_IDENTIFIER,
    IDEA_REMOTE_DATE_FORMAT,
    DEFAULT_DATE_FORMAT,
)
from .models import ExchangeOffice, Bank, Rate

import logging
logger = logging.getLogger(__name__)


class IdeaBankLoader(BaseLoader):
    def get_expected_exchange_offices(self):
        return ExchangeOffice.objects.filter(identifier=IDEABANK_ONLINE_OFFICE)

    def _extract(self, today: datetime.date) -> Optional[Dict]:
        response = self.client.post(IDEABANK_URL, data={
            'date': today.strftime(IDEA_REMOTE_DATE_FORMAT),
            'id': 70,
        }, headers={
            'X-Requested-With': 'XMLHttpRequest',
        }, timeout=DEFAULT_TIMEOUT)

        try:
            raw_rates = response.json()['data']
        except (JSONDecodeError, KeyError) as e:
            logger.info(
                'Unexpected rates response caused %s: %s',
                type(e).__name__,
                response.content
            )
            return None

        return raw_rates.get('rates')

    def _load(self) -> bool:
        today = datetime.date.today()

        raw_rates = self._extract(today)
        if not raw_rates:
            logger.info('No rates for today.')
            return False

        last_rates = max(raw_rates.items(), key=lambda x: x[0])

        office_name = '{} {}'.format(today.strftime(DEFAULT_DATE_FORMAT), last_rates[0])
        raw_rates = last_rates[1]

        try:
            bank = Bank.objects.get(identifier=IDEABANK_IDENTIFIER)
        except Bank.DoesNotExist:
            logger.error('IdeaBank identifier does not exist in DB')
            return False

        office = ExchangeOffice.objects.filter(identifier=IDEABANK_ONLINE_OFFICE, bank=bank).first()

        if office and office.address == office_name:
            return False

        if not office:
            office = ExchangeOffice(identifier=IDEABANK_ONLINE_OFFICE, bank=bank)

        office.address = office_name
        office.save()
        self.add_office(office.id)

        for raw_currency, raw_currency_rates in raw_rates.items():
            if 'USD' in raw_currency:
                currency = Rate.USD
            elif 'EUR' in raw_currency:
                currency = Rate.EUR
            else:
                raise ValueError('Unknown currency: {}'.format(raw_currency))

            for raw_currency_rate in raw_currency_rates.values():
                buy = raw_currency_rate['Operation'] == '1'
                rate = raw_currency_rate['Value']
                self.add_rate(Rate(rate=rate, buy=buy, currency=currency, exchange_office=office))

        return True






