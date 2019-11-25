from decimal import Decimal
from unittest.mock import patch

import pytest

from exchange.factories import ExchangeOfficeFactory, RateFactory
from exchange.models import Rate, Bank
from exchange.selectby import SelectbyLoader
from lxml import html
import os


original_fromstring = html.fromstring


def patched_standard_page(*args, **kwargs):
    with open(os.path.join(os.path.dirname(__file__), 'data', 'selectby.html'), mode='rb') as f:
        return original_fromstring(f.read())


def patched_20191125_page(*args, **kwargs):
    with open(os.path.join(os.path.dirname(__file__), 'data', 'selectby-20191125.html'), mode='rb') as f:
        return original_fromstring(f.read())



class TestSelectbyLoader:
    @pytest.mark.django_db
    @patch('lxml.html.fromstring', patched_standard_page)
    @patch('exchange.selectby.update_all_coordinates')
    def test_load(self, patched_update_all_coordinates):
        fake_office = ExchangeOfficeFactory(identifier='5')
        real_office = ExchangeOfficeFactory(identifier='478')
        my_office = ExchangeOfficeFactory(identifier='1011')

        RateFactory(exchange_office=real_office, rate='5.5', buy=True, currency=Rate.USD)
        RateFactory(exchange_office=my_office, rate='3.5', buy=True, currency=Rate.USD)

        SelectbyLoader().load()

        fake_office.refresh_from_db()
        real_office.refresh_from_db()
        my_office.refresh_from_db()

        assert fake_office.is_removed
        assert not real_office.is_removed
        assert not my_office.is_removed
        assert patched_update_all_coordinates.called

        assert (
            Rate.objects.get(exchange_office__identifier='478', buy=True, currency=Rate.USD).rate ==
            Decimal('1.875')
        )
        assert real_office.rate_set.count() != 1

    @pytest.mark.django_db
    @patch('lxml.html.fromstring', patched_20191125_page)
    @patch('exchange.selectby.update_all_coordinates')
    def test_load__20191125(self, patched_update_all_coordinates):
        SelectbyLoader().load()

        assert Bank.objects.all().count() == 21
        assert patched_update_all_coordinates.called
