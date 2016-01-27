from uuid import uuid4

from django.shortcuts import render, redirect
from django.http.response import HttpResponseRedirect
from django.core.urlresolvers import reverse

from exchange.models import UserInfo, Rate
from exchange.utils import get_client_ip, set_name_cookie, get_best_rates, get_username
from .forms import UserInfoForm


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
        if not userinfo:
            if username:
                userinfo = UserInfo.objects.create(name=username, ip=get_client_ip(request))
            else:
                userinfo = UserInfo.objects.create(ip=get_client_ip(request))
        form = UserInfoForm(instance=userinfo)
        return set_name_cookie(render(request, 'index.html', {
            'form': form,
        }), userinfo.name)
    elif request.method == 'POST':
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


def get_rates(request):
    username = get_username(request)
    print(username)
    if not username:
        return redirect('config')
    try:
        user = UserInfo.objects.get(name=username)
    except UserInfo.DoesNotExist:
        return HttpResponseRedirect(reverse('config') + '?name=' + username)
    offices = user.exchange_offices.all()
    for office in offices:
        office.rates = office.rate_set.order_by('currency', '-buy')
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




