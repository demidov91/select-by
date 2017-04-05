import json
from decimal import Decimal

from .defines import MTBANK_68_BODY, MTBANK_COMMON_BODY, MTBANK_68_OFFICE, MTBANK_COMMON_OFFICE, MTBANK_IDENTIFIER,\
    MTBANK_RATES_START_LINE

from .models import ExchangeOffice, Bank, Rate
from .utils import BaseLoader

import logging
logger = logging.getLogger(__name__)


class MtbankLoader(BaseLoader):
    def get_expected_exchange_offices(self):
        return ExchangeOffice.objects.filter(identifier__in=(MTBANK_COMMON_OFFICE, MTBANK_68_OFFICE))

    def _load(self) -> bool:
        return self._load_office(MTBANK_COMMON_BODY, MTBANK_COMMON_OFFICE, 'common') or \
               self._load_office(MTBANK_68_BODY, MTBANK_68_OFFICE, 'РКЦ-68')

    def _load_office(self, request_body, office_identifier, office_address) -> bool:
        response = self.client.post(
            'https://www.mtbank.by/_run.php?xoadCall=true',
            data=request_body.encode('utf-8'),
            headers={
                'Accept': 'text/html; charset=UTF-8',
                'Content-Type': 'text/plain; charset=UTF-8',
            })
        response_line = response.text
        start_position = response_line.find(MTBANK_RATES_START_LINE)
        if start_position < 0:
            logger.error('Illegal format')
            return False

        start_position += len(MTBANK_RATES_START_LINE)
        end_position = start_position
        brackets_counter = 0
        while end_position < len(response_line):
            if response_line[end_position] == '{':
                brackets_counter += 1
            elif response_line[end_position] == '}':
                brackets_counter -= 1
            end_position += 1
            if brackets_counter == 0:
                break
        else:
            logger.error('Illegal format')
            return False
        try:
            office = ExchangeOffice.objects.get_or_create(identifier=office_identifier,
                                                          address=office_address,
                                                          bank=Bank.objects.get(identifier=MTBANK_IDENTIFIER))[0]
        except Bank.DoesNotExist:
            logger.error('MTBank identifier does not exist in DB')
            return False

        self._offices.append(office.id)
        all_rates = json.loads(response_line[start_position:end_position])
        for curr_key, curr_val in ('USD', Rate.USD), ('EUR', Rate.EUR), ('RUB', Rate.RUB):
            self._rates.append(Rate(exchange_office=office, currency=curr_val, buy=True,
                                        rate=Decimal(all_rates[curr_key + 'BYN']['Rate'])))
            self._rates.append(Rate(exchange_office=office, currency=curr_val, buy=False,
                                        rate=Decimal(all_rates['BYN' + curr_key]['Rate'])))

        return True


