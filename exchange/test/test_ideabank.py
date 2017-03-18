from decimal import Decimal
from unittest.mock import patch
import datetime

from django.test import TestCase
from exchange.models import Bank, ExchangeOffice, Rate
from exchange.defines import IDEABANK_IDENTIFIER, IDEABANK_ONLINE_OFFICE
from exchange.ideabank import IdeaBankLoader
from .data.ideabank import JSON_RESPONSE
from exchange.factories import BankFactory, RateFactory, ExchangeOfficeFactory


class ResponseMock:
    def __init__(self, *args, **kwargs):
        pass

    def json(self):
        return JSON_RESPONSE


class MockDate(datetime.date):
    @classmethod
    def today(cls):
        return cls(2017, 3, 17)


class IdeaBankLoaderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bank = BankFactory(identifier=IDEABANK_IDENTIFIER)

    @patch('requests.sessions.Session.post', side_effect=ResponseMock)
    @patch('datetime.date', new=MockDate)
    def test_load__new_rates(self, *args):
        IdeaBankLoader().load()

        office = ExchangeOffice.objects.get(identifier=IDEABANK_ONLINE_OFFICE)
        self.assertEqual('17.03.2017 19:00:00', office.address)
        self.assertEqual(Decimal('1.8840'), Rate.objects.get(exchange_office=office, buy=True, currency=Rate.USD).rate)
        self.assertEqual(Decimal('1.8910'), Rate.objects.get(exchange_office=office, buy=False, currency=Rate.USD).rate)
        self.assertEqual(Decimal('2.0210'), Rate.objects.get(exchange_office=office, buy=True, currency=Rate.EUR).rate)
        self.assertEqual(Decimal('2.0390'), Rate.objects.get(exchange_office=office, buy=False, currency=Rate.EUR).rate)

    @patch('requests.sessions.Session.post', side_effect=ResponseMock)
    @patch('datetime.date', new=MockDate)
    def test_load__update_rates(self, *args):
        office = ExchangeOfficeFactory(bank=self.bank, identifier=IDEABANK_ONLINE_OFFICE, address='17.03.2017 18:59:00')
        RateFactory(exchange_office=office, buy=True, currency=Rate.USD, rate='1.883')

        IdeaBankLoader().load()

        office = ExchangeOffice.objects.get(identifier=IDEABANK_ONLINE_OFFICE)
        self.assertEqual('17.03.2017 19:00:00', office.address)
        self.assertEqual(Decimal('1.8840'), Rate.objects.get(exchange_office=office, buy=True, currency=Rate.USD).rate)

