from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from ..factories import ExchangeOfficeFactory, RateFactory
from ..models import Rate
from ..selectby import SelectbyLoader
from lxml import html
import os


class PatchedHtmlParse:
    def __init__(self, *args, **kwargs):
        super(PatchedHtmlParse, self).__init__()

    def getroot(self):
        with open(os.path.join(os.path.dirname(__file__), 'data', 'selectby.html'), mode='rb') as f:
            return html.fromstring(f.read())


class SelectbyLoaderTest(TestCase):
    @patch('lxml.html.parse', PatchedHtmlParse)
    def test_load(self):
        fake_office = ExchangeOfficeFactory(identifier='5')
        real_office = ExchangeOfficeFactory(identifier='478')
        my_office = ExchangeOfficeFactory(identifier='1011')

        RateFactory(exchange_office=real_office, rate='5.5', buy=True, currency=Rate.USD)
        RateFactory(exchange_office=my_office, rate='3.5', buy=True, currency=Rate.USD)

        SelectbyLoader().load()

        fake_office.refresh_from_db()
        real_office.refresh_from_db()
        my_office.refresh_from_db()

        self.assertTrue(fake_office.is_removed)
        self.assertFalse(real_office.is_removed)
        self.assertFalse(my_office.is_removed)

        self.assertEqual(
            Decimal('1.875'),
            Rate.objects.get(exchange_office__identifier='478', buy=True, currency=Rate.USD).rate
        )

        self.assertEqual(1, my_office.rate_set.count())