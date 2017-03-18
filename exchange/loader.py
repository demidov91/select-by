from .models import Rate, ExchangeOffice
from django.db.models import Q
from django.db.transaction import atomic

from .mtbank import MtbankLoader
from .ideabank import IdeaBankLoader
from .selectby import SelectbyLoader

import logging
logger = logging.getLogger(__name__)


class RatesLoader:
    def __init__(self):
        self.bank_rates = []
        self.fresh_offices = set()

    def _save(self):
        Rate.objects.filter(exchange_office__in=self.fresh_offices).delete()
        Rate.objects.bulk_create(self.bank_rates)
        ExchangeOffice.objects.filter(~Q(id__in=self.fresh_offices)).update(is_removed=True)
        ExchangeOffice.objects.filter(id__in=self.fresh_offices).update(is_removed=False)

    @atomic
    def load(self):
        for loader_class in (SelectbyLoader, MtbankLoader, IdeaBankLoader):
            loader = loader_class()
            something_has_changed = loader.load()
            if something_has_changed:
                logger.info('{} data will be updated.'.format(loader_class.__name__))
            else:
                logger.info("{} data won't be updated.".format(loader_class.__name__))

            self.fresh_offices.update(loader.get_offices())
            self.bank_rates.extend(loader.get_rates())

        self._save()