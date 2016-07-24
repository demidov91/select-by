from xml.etree import ElementTree as ET
from urllib.request import urlopen
import datetime

from django.core.management.base import BaseCommand

from ...defines import NBRB_URL
from ...utils import get_dynamic_setting, save_rates
from ...models import DynamicSettings


import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Loads last rates form http://select.by'

    def handle(self, *args, **options):
        stored_date = get_dynamic_setting(DynamicSettings.NBRB_RATES_DATE)
        if stored_date:
            if datetime.datetime.strptime(stored_date, '%m/%d/%Y').date() > datetime.date.today():
                logger.info('New rated are already stored.')
                return
        doc = ET.fromstring(urlopen(NBRB_URL).read().decode('utf-8'))
        currency_date = doc.get('Date')
        if stored_date != currency_date:
            logger.info('New NBRB rates will be saved.')
            save_rates(doc)
