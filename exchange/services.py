from typing import Iterable

from exchange.models import ExchangeOffice


def set_exchange_offices(request, exchange_offices: Iterable[ExchangeOffice]):
    """
    Takes care about a storage: session for non-authenticated, db for authenticated.
    """

    if request.user.is_authenticated:
        request.user.exchange_offices.set(exchange_offices)

    else:
        request.session['exchange_offices'] = [x.id for x in exchange_offices]
