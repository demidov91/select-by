"""
Unsorted utils.
"""

import logging
from decimal import Decimal

import requests
from django.db.transaction import atomic
from django.template.defaulttags import register

from exchange.models import Rate, ExchangeOffice


logger = logging.getLogger(__name__)


def quantize_to_cents(original: Decimal) -> Decimal:
    cent_amount = original.quantize(Decimal('1.00'))
    if original != cent_amount:
        return original
    return cent_amount


@register.filter
def get_item(dictionary, key):
    """
    Just don't wont to create separate package for one template filter...
    """
    return dictionary.get(key)


class BaseLoader:
    def __init__(self):
        self.client = requests.session()
        self._offices = []
        self._rates = []

    def add_office(self, *office_id):
        self._offices.extend(office_id)

    def add_rate(self, *rate: Rate):
        self._rates.extend(rate)

    def get_offices(self):
        return self._offices

    def get_rates(self):
        return self._rates

    def get_expected_exchange_offices(self):
        return ExchangeOffice.objects.none()

    def _load(self) ->bool:
        raise NotImplementedError()

    @atomic
    def load(self):
        is_updated = self._load()
        if is_updated:
            logger.info('%s data will be updated.', self.__class__.__name__)
            Rate.objects.filter(exchange_office__in=self.get_offices()).delete()
            Rate.objects.bulk_create(self.get_rates())
            self.get_expected_exchange_offices().exclude(
                id__in=self.get_offices()
            ).update(
                is_removed=True
            )
            ExchangeOffice.objects.filter(id__in=self.get_offices()).update(is_removed=False)
        else:
            logger.info("%s data won't be updated.", self.__class__.__name__)
