from factory.django import DjangoModelFactory
from factory import SubFactory, Sequence

from .models import ExchangeOffice, Bank, Rate


class BankFactory(DjangoModelFactory):
    class Meta:
        model = Bank

    identifier = Sequence(lambda x: 'Bank %s' % x)


class ExchangeOfficeFactory(DjangoModelFactory):
    class Meta:
        model = ExchangeOffice

    identifier = Sequence(lambda x: 'Office %s' % x)
    address = 'Any address'
    bank = SubFactory(BankFactory)


class RateFactory(DjangoModelFactory):
    class Meta:
        model = Rate

    exchange_office = SubFactory(ExchangeOffice)


