from exchange.models import ExchangeOffice

def get_exchange_offices(request):
    if request.user.is_authenticated:
        return request.user.exchange_offices.all()

    return ExchangeOffice.objects.filter(id__in=request.session.get('exchange_offices', []))


def get_exchnage_offices_id(request):
    return get_exchange_offices(request).values_list('id', flat=True)