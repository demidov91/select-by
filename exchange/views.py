from django.shortcuts import render, get_object_or_404, redirect
from django.http.response import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from exchange.models import UserInfo, Rate
from exchange.utils import create_new_user, get_client_ip
from .forms import UserInfoForm


import logging
logger = logging.getLogger(__name__)


def overview(request):
    if request.method == 'GET':
        username = request.GET.get('name')
        if not username and request.COOKIES.get('name'):
            return HttpResponseRedirect(reverse('config') + '?name=' + request.COOKIES.get('name'))
        userinfo = None
        if username:
            try:
                userinfo = UserInfo.objects.get(user__username=username)
            except UserInfo.DoesNotExist:
                logger.info('{} does not exist'.format(userinfo))
        if not userinfo:
            if username:
                userinfo = UserInfo.objects.create(user=User.objects.create(username=username), ip=get_client_ip(request))
            else:
                userinfo = UserInfo.objects.create(user=create_new_user(), ip=get_client_ip(request))
        form = UserInfoForm(instance=userinfo)
        if not username:
            form.fields['name'].initial = None
        response = render(request, 'index.html', {
            'form': form,
        })
        response.set_cookie('name', userinfo.user.username)
        return response
    elif request.method == 'POST':
        instance = UserInfo.objects.get(id=request.POST['id'])
        form = UserInfoForm(instance=instance, data=request.POST)
        if form.is_valid():
            instance = form.save()
            if instance:
                response = HttpResponseRedirect(reverse('rates') + '?name=' + instance.user.username)
                response.set_cookie('name', instance.user.username)
                return response
        return render(request, 'index.html', {
            'form': form,
        })


def get_rates(request):
    user = get_object_or_404(UserInfo.objects, user__username=request.GET.get('name'))
    offices = user.exchange_offices.all()
    for office in offices:
        office.rates = office.rate_set.order_by('currency', '-buy')
    return render(request, 'rates.html', {'offices': offices})




