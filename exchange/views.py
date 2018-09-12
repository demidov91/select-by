import logging
from decimal import Decimal

from django.shortcuts import render, redirect
from django.http.response import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import View

from exchange.models import UserInfo, Rate, DynamicSettings, ExchangeOffice
from exchange.utils import get_client_ip, set_name_cookie, get_best_rates, get_username
from .forms import UserInfoForm


logger = logging.getLogger(__name__)


class OverView(View):
    def get(self, request):
        username = get_username(request)
        userinfo = None
        if username:
            try:
                userinfo = UserInfo.objects.get(name=username)
            except UserInfo.DoesNotExist:
                logger.info('%s does not exist', userinfo)
        if not userinfo and username:
            userinfo = UserInfo.objects.create(name=username, ip=get_client_ip(request))
        form = UserInfoForm(instance=userinfo)
        return set_name_cookie(render(request, 'index.html', {
            'form': form,
            'exists': userinfo and userinfo.exchange_offices.all().exists(),
        }), userinfo and userinfo.name)

    def post(self, request):
        instance = None
        if request.POST.get('id'):
            instance = UserInfo.objects.get(id=request.POST['id'])
        form = UserInfoForm(instance=instance, data=request.POST)
        if form.is_valid():
            form.instance.ip = get_client_ip(request)
            instance = form.save()
            return set_name_cookie(HttpResponseRedirect(reverse('rates') + '?name=' + instance.name), instance.name)
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
        'dynamic_settings': dict(DynamicSettings.objects.all().values_list('key', 'value')),
    }), user.name)


@require_GET
def my_points(request):
    return JsonResponse({
        'exchange': [{
            'coordinates': (x.latitude, x.longitude),
        } for x in ExchangeOffice.objects.filter(is_removed=False)],
    })
