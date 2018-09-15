import logging
from decimal import Decimal
from typing import Iterable

from django.db.transaction import atomic

from exchange.models import DynamicSettings, ExchangeOffice


logger = logging.getLogger(__name__)


def set_exchange_offices(request, exchange_offices: Iterable[ExchangeOffice]):
    """
    Takes care about a storage: session for non-authenticated, db for authenticated.
    """

    if request.user.is_authenticated:
        request.user.exchange_offices.set(exchange_offices)

    else:
        request.session['exchange_offices'] = [x.id for x in exchange_offices]


def _set_or_create(model_class, keys: dict, values: dict):
    if model_class.objects.filter(**keys).exists():
        model_class.objects.filter(**keys).update(**values)
    else:
        keys.update(values)
        model_class.objects.create(**keys)


def set_dynamic_setting(key: str, value: str):
    _set_or_create(DynamicSettings, {'key': key}, {'value': value})


NBRB_CURRENCY_TO_DYNAMIC_SETTING = {
    '145': DynamicSettings.NBRB_USD,
    '292': DynamicSettings.NBRB_EUR,
    '298': DynamicSettings.NBRB_RUB,
}


@atomic
def save_nbrb_rates(doc):
    set_dynamic_setting(DynamicSettings.NBRB_RATES_DATE, doc.get('Date'))
    for rate in filter(lambda x: x.get('Id') in NBRB_CURRENCY_TO_DYNAMIC_SETTING.keys(), doc):
        value = scale = None
        for field in rate:
            if field.tag == 'Rate':
                value = Decimal(field.text)
            elif field.tag == 'Scale':
                scale = int(field.text)
        if (value or scale) is None:
            logger.error('Broken rate!')
            raise ValueError('Broken {} rate.'.format(rate.get('Id')))
        set_dynamic_setting(NBRB_CURRENCY_TO_DYNAMIC_SETTING[rate.get('Id')], value/scale)
