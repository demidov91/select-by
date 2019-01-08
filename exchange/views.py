import logging

from django.db.models import Q
from django.shortcuts import render, redirect
from django.http.response import JsonResponse, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET, require_POST

from exchange.constants import ONLINE_EXCHANGE_OFFICES_NAMES, ONLINE_EXCHANGE_OFFICES_IDENTIFIERS
from exchange.models import Rate, DynamicSettings, ExchangeOffice
from exchange.services import set_exchange_offices
from exchange.utils.exchange_office import (
    get_exchange_offices,
    get_exchnage_offices_id,
    get_online_exchange_offices,
)
from exchange.utils.common import quantize_to_cents
from exchange.utils.rate import get_best_rates
from exchange.utils.user import has_social_account
from exchange.constants import BANK_NAME_TO_SHORT_NAME


logger = logging.getLogger(__name__)


def config(request):
    active_id = get_exchnage_offices_id(request)

    online_exchange_offices_data = tuple({
        'id': x.id,
        'name': ONLINE_EXCHANGE_OFFICES_NAMES.get(x.identifier),
        'is_selected': x.id in active_id,
    } for x in get_online_exchange_offices())

    return render(request, 'config.html', {
        'is_authenticated': request.user.is_authenticated,
        'has_social_account': has_social_account(request.user),
        'has_exchange_offices': get_exchange_offices(request).exists(),
        'online': online_exchange_offices_data,
    })


@require_GET
def get_rates(request):
    offices = get_exchange_offices(request)

    if not offices.exists():
        return redirect('config')

    for office in offices:
        office.rates = office.rate_set.order_by('currency', '-buy')
        for rate in office.rates:
            rate.rate = quantize_to_cents(rate.rate)

    best_rates = []
    for currency in (x[0] for x in Rate.CURRENCIES):
        best_rates.extend(get_best_rates(currency, offices.filter(is_removed=False), True))
        best_rates.extend(get_best_rates(currency, offices.filter(is_removed=False), False))

    for office in offices:
        for best_rate in filter(lambda x: x in best_rates, office.rates):
            best_rate.is_best = True

    return render(request, 'rates.html', {
        'offices': offices,
        'dynamic_settings': dict(DynamicSettings.objects.all().values_list('key', 'value')),
        'is_authenticated': request.user.is_authenticated,
        'has_social_account': has_social_account(request.user),
    })


@require_GET
def my_points(request):
    points_id = get_exchnage_offices_id(request)

    return JsonResponse({
        'exchange': [{
            'coordinates': (x.latitude, x.longitude),
            'id': x.id,
            'isSelected': x.id in points_id,
            'content': BANK_NAME_TO_SHORT_NAME.get(x.bank.name),
            'bank': x.bank.name,
            'address': x.address,
        } for x in ExchangeOffice.objects.filter(
            Q(is_removed=False),
            ~Q(identifier__in=ONLINE_EXCHANGE_OFFICES_IDENTIFIERS),
        ).select_related('bank')],
    })


@require_POST
def save_points(request):
    id_list = request.POST.getlist('points[]', [])
    id_list.extend(get_exchange_offices(request).filter(is_removed=True).values_list('id', flat=True))

    points = ExchangeOffice.objects.filter(id__in=id_list)
    set_exchange_offices(request, exchange_offices=points)

    return HttpResponse()
