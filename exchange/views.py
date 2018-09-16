import logging
from decimal import Decimal

from django.shortcuts import render, redirect
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST

from exchange.models import Rate, DynamicSettings, ExchangeOffice
from exchange.services import set_exchange_offices
from exchange.utils.exchange_office import (
    get_exchange_offices,
    get_exchnage_offices_id,
)
from exchange.utils.common import quantize_to_cents
from exchange.utils.rate import get_best_rates
from exchange.constants import BANK_NAME_TO_SHORT_NAME


logger = logging.getLogger(__name__)


def config(request):
    return render(request, 'config.html', {
        'is_authenticated': request.user.is_authenticated,
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
        best_rates.extend(get_best_rates(currency, offices, True))
        best_rates.extend(get_best_rates(currency, offices, False))

    for office in offices:
        for best_rate in filter(lambda x: x in best_rates, office.rates):
            best_rate.is_best = True

    return render(request, 'rates.html', {
        'offices': offices,
        'dynamic_settings': dict(DynamicSettings.objects.all().values_list('key', 'value')),
        'is_authenticated': request.user.is_authenticated,
        'has_social_account': (
            request.user.is_authenticated and request.user.socialaccount_set.exists()
        ),
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
        } for x in ExchangeOffice.objects.filter(is_removed=False).select_related('bank')],
    })


@require_POST
def save_points(request):
    id_list = request.POST.getlist('points[]', [])
    id_list.extend(get_exchange_offices(request).filter(is_removed=True).values_list('id', flat=True))

    points = ExchangeOffice.objects.filter(id__in=id_list)
    set_exchange_offices(request, exchange_offices=points)

    return HttpResponse()
