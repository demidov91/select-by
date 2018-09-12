import os
from decimal import Decimal

from exchange.coordinates_loader import extract_coordinates_from_page


def test_extract_coordinates_from_page():
    with open(
            os.path.join(os.path.dirname(__file__), 'data', 'id476.html'),
            mode='rt',
            encoding='windows-1251'
    ) as f:
        content = f.read()

    assert extract_coordinates_from_page(content) == (Decimal('53.914022'), Decimal('27.552623'))
