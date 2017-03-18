import base64
from decimal import Decimal
import requests
from django.db.models import Min, Max, Q
from django.db.transaction import atomic
from django.template.defaulttags import register

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
    '292': DynamicSettings.NBRB_EUR,
    '298': DynamicSettings.NBRB_RUB,
}


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
            logger.info('{} data will be updated.'.format(self.__class__.__name__))
            Rate.objects.filter(exchange_office__in=self.get_offices()).delete()
            Rate.objects.bulk_create(self.get_rates())
            self.get_expected_exchange_offices().exclude(id__in=self.get_offices()).update(is_removed=True)
            ExchangeOffice.objects.filter(id__in=self.get_offices()).update(is_removed=False)
        else:
            logger.info("{} data won't be updated.".format(self.__class__.__name__))