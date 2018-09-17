from exchange.constants import ONLINE_EXCHANGE_OFFICES_IDENTIFIERS
from exchange.models import ExchangeOffice


def get_exchange_offices(request):
    if request.user.is_authenticated:
        return request.user.exchange_offices.all()

    return ExchangeOffice.objects.filter(id__in=request.session.get('exchange_offices', []))


def get_exchnage_offices_id(request):
    return get_exchange_offices(request).values_list('id', flat=True)


def get_online_exchange_offices(only_live: bool=False):
    qs = ExchangeOffice.objects.filter(identifier__in=ONLINE_EXCHANGE_OFFICES_IDENTIFIERS)
    if only_live:
        qs = qs.filter(is_removed=False)

    return qs
