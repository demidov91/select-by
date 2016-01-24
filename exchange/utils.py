from urllib.request import urlopen

from django.conf import settings

from exchange.models import DynamicSettings

import logging
logger = logging.getLogger(__name__)


def get_dynamic_setting(key: str) -> str:
    try:
        return DynamicSettings.objects.get(key=key).value
    except DynamicSettings.DoesNotExist:
        return None


def set_dynamic_setting(key: str, value: str):
    if DynamicSettings.objects.filter(key=key).exists():
        DynamicSettings.objects.filter(key=key).udpate(value=value)
    else:
        DynamicSettings.objects.create(key=key, value=value)


class RatesLoader:
    raw_rows = []
    last_update = ''

    def load(self):
        self.parse_full_page(self.load_page_source())
        if get_dynamic_setting(DynamicSettings.LAST_UPDATE_KEY) == self.last_update:
            return
        set_dynamic_setting(DynamicSettings.LAST_UPDATE_KEY, self.last_update)

    def load_page_source(self):
        return urlopen(settings.RATES_SOURCE).read().decode('utf-8')

