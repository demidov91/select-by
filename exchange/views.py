from decimal import Decimal

from django.shortcuts import render, redirect
from django.http.response import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page

from exchange.models import UserInfo, Rate, DynamicSettings
from exchange.utils import get_client_ip, set_name_cookie, get_best_rates, get_username, get_dynamic_setting, save_rates
from .forms import UserInfoForm
from .defines import NBRB_URL

from xml.etree import ElementTree as ET
from urllib.request import urlopen


import logging
logger = logging.getLogger(__name__)


def overview(request):
    if request.method == 'GET':
        username = get_username(request)
        userinfo = None
        if username:
            try:
                userinfo = UserInfo.objects.get(name=username)
            except UserInfo.DoesNotExist:
                logger.info('{} does not exist'.format(userinfo))
        if not userinfo and username:
            userinfo = UserInfo.objects.create(name=username, ip=get_client_ip(request))
        form = UserInfoForm(instance=userinfo)
        return set_name_cookie(render(request, 'index.html', {
            'form': form,
        }), userinfo and userinfo.name)
    elif request.method == 'POST':
        instance = None
        if request.POST.get('id'):
            instance = UserInfo.objects.get(id=request.POST['id'])
        form = UserInfoForm(instance=instance, data=request.POST)
        if form.is_valid():
            form.instance.ip = get_client_ip(request)
            instance = form.save()
            if instance:
                return set_name_cookie(HttpResponseRedirect(reverse('rates') + '?name=' + instance.name),
                                       instance.name)
        return render(request, 'index.html', {
            'form': form,
        })


def _quantize_to_cents(original: Decimal) -> Decimal:
    cent_amount = original.quantize(Decimal('1.00'))
    if original != cent_amount:
        return original
    return cent_amount


@require_GET
def get_rates(request):
    username = get_username(request)
    if not username:
        return redirect('config')
    try:
        user = UserInfo.objects.get(name=username)
    except UserInfo.DoesNotExist:
        return HttpResponseRedirect(reverse('config') + '?name=' + username)
    offices = user.exchange_offices.all()
    for office in offices:
        office.rates = office.rate_set.order_by('currency', '-buy')
        for rate in office.rates:
            rate.rate = _quantize_to_cents(rate.rate)
    best_rates = []
    for currency in (x[0] for x in Rate.CURRENCIES):
        best_rates.extend(get_best_rates(currency, user.exchange_offices.all(), True))
        best_rates.extend(get_best_rates(currency, user.exchange_offices.all(), False))
    for office in offices:
        for best_rate in filter(lambda x: x in best_rates, office.rates):
            best_rate.is_best = True
    return set_name_cookie(render(request, 'rates.html', {
        'offices': offices,
        'name': user.name,
    }), user.name)


@require_GET
@cache_page(15 * 60)
def get_nbrb_rates(request):
    logger.info('get_nbrb_rates method is called.')
    doc = ET.fromstring(urlopen(NBRB_URL).read().decode('utf-8'))
    currency_date = doc.get('Date')
    if get_dynamic_setting(DynamicSettings.NBRB_RATES_DATE) != currency_date:
        logger.info('New NBRB rates will be saved.')
        save_rates(doc)
    return JsonResponse({
        'USD': get_dynamic_setting(DynamicSettings.NBRB_USD),
        'EUR': get_dynamic_setting(DynamicSettings.NBRB_EUR),
        'RUB': get_dynamic_setting(DynamicSettings.NBRB_RUB),
        'for_date': get_dynamic_setting(DynamicSettings.NBRB_RATES_DATE),
    })









