from decimal import Decimal
from unittest.mock import patch
from unittest import mock
import datetime

from django.test import TestCase
from exchange.models import Bank, ExchangeOffice, Rate
from exchange.defines import IDEABANK_IDENTIFIER, IDEABANK_ONLINE_OFFICE
from exchange.ideabank import IdeaBankLoader


class ResponseMock:
    def __init__(self, *args, **kwargs):
        pass

    def json(self):
        return {
            "data":{
                "ratesnb":{"1 USD":"1.8981","1 EUR":"2.0341","100 RUB":"3.2595","10 PLN":"4.7149"},
                "rates": {
                    "19:00:00":{
                        "1 USD":{
                            "1":{"Value":"1.8840","Currency":"USD","Units":"1","Operation":"1"},
                            "2":{"Value":"1.8910","Currency":"USD","Units":"1","Operation":"2"}
                        },
                        "1 EUR":{
                            "1":{"Value":"2.0210","Currency":"EUR","Units":"1","Operation":"1"},
                            "2":{"Value":"2.0390","Currency":"EUR","Units":"1","Operation":"2"}
                        }
                    },
                    "14:15:00":{
                        "1 USD":{
                            "1":{"Value":"1.8840","Currency":"USD","Units":"1","Operation":"1"},
                            "2":{"Value":"1.8920","Currency":"USD","Units":"1","Operation":"2"}
                        },
                        "1 EUR":{
                            "1":{"Value":"2.0230","Currency":"EUR","Units":"1","Operation":"1"},
                             "2":{"Value":"2.0390","Currency":"EUR","Units":"1","Operation":"2"}
                        }
                    },"09:30:00":{
                        "1 USD":{
                            "1":{"Value":"1.8860","Currency":"USD","Units":"1","Operation":"1"},
                            "2":{"Value":"1.8940","Currency":"USD","Units":"1","Operation":"2"}
                        },
                        "1 EUR":{
                            "1":{"Value":"2.0230","Currency":"EUR","Units":"1","Operation":"1"},
                            "2":{"Value":"2.0420","Currency":"EUR","Units":"1","Operation":"2"}
                        }
                    },"08:50:00":{
                        "1 USD":{
                            "1":{"Value":"1.8910","Currency":"USD","Units":"1","Operation":"1"},
                            "2":{"Value":"1.9010","Currency":"USD","Units":"1","Operation":"2"}
                        },
                        "1 EUR":{
                            "1":{"Value":"2.0230","Currency":"EUR","Units":"1","Operation":"1"},
                            "2":{"Value":"2.0420","Currency":"EUR","Units":"1","Operation":"2"}
                        }
                    }
                }
            }
        }


class MockDate(datetime.date):
    @classmethod
    def today(cls):
        return cls(2017, 3, 17)


class IdeaBankLoaderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Bank.objects.get_or_create(identifier=IDEABANK_IDENTIFIER)[0]

    @patch('requests.sessions.Session.post', side_effect=ResponseMock)
    @patch('datetime.date', new=MockDate)
    def test_load__new_rates(self, *args):
        loader = IdeaBankLoader()
        self.assertTrue(loader.load())

        self.assertEqual(1, len(loader.get_offices()))
        self.assertEqual(4, len(loader.get_rates()))
        office = ExchangeOffice.objects.get(identifier=IDEABANK_ONLINE_OFFICE)

        self.assertEqual(office.id, loader.get_offices()[0])
        usd_rates = {}
        eur_rates = {}

        for rate in loader.get_rates():
            self.assertEqual(office, rate.exchange_office)
            if rate.currency == Rate.USD:
                usd_rates[rate.buy] = rate.rate
            else:
                eur_rates[rate.buy] = rate.rate

        self.assertEqual('IdeaBank online 17.03.2017 19:00:00', office.address)
        self.assertEqual('1.8840', usd_rates[True])
        self.assertEqual('1.8910', usd_rates[False])
        self.assertEqual('2.0210', eur_rates[True])
        self.assertEqual('2.0390', eur_rates[False])

