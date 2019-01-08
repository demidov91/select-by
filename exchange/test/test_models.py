import pytest

from exchange.models import ExchangeOffice

class TestExchangeOffice:
    @pytest.mark.parametrize('kw,expected', [
        ({
            'latitude': 21.1,
            'longitude': 51.1,
        }, True),
        ({
             'latitude': 21.1,
         }, False),
        ({}, False),

    ])
    def test_has_valid_coordinates(self, kw, expected):
        assert ExchangeOffice(**kw).has_valid_coordinates is expected