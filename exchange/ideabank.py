import datetime

from .utils import BaseLoader
from .defines import IDEABANK_URL, IDEABANK_ONLINE_OFFICE, IDEABANK_IDENTIFIER, IDEA_REMOTE_DATE_FORMAT,\
    DEFAULT_DATE_FORMAT
from .models import ExchangeOffice, Bank, Rate

import logging
logger = logging.getLogger(__name__)


class IdeaBankLoader(BaseLoader):

    def load(self):
        today = datetime.date.today()

        response = self.client.post(IDEABANK_URL, data={
            'date': today.strftime(IDEA_REMOTE_DATE_FORMAT),
            'id': 70,
        })

        raw_rates = response.json()['data']

        if 'rates' not in raw_rates:
            return False

        last_rates = max(raw_rates['rates'].items(), key=lambda x: x[0])

        office_name = 'IdeaBank online {} {}'.format(today.strftime(DEFAULT_DATE_FORMAT), last_rates[0])
        raw_rates = last_rates[1]

        try:
            bank = Bank.objects.get(identifier=IDEABANK_IDENTIFIER)
        except Bank.DoesNotExist:
            logger.error('IdeaBank identifier does not exist in DB')
            return

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






