from uuid import uuid4

from exchange.models import UserInfo, Rate
from exchange.utils import create_new_user, get_client_ip

from django.shortcuts import render, get_object_or_404

import logging
logger = logging.getLogger(__name__)


def overview(request):
    username = request.GET.get('username', request.COOKIES.get('username'))
    userinfo = None
    if username:
        try:
            userinfo = UserInfo.objects.get(user__username=username)
        except UserInfo.DoesNotExist:
            logger.info('{} does not exist'.format(userinfo))
    if not userinfo:
        userinfo = UserInfo.objects.create(user=create_new_user(), ip=get_client_ip(request))
    return None


def get_rates(request):
    user = get_object_or_404(UserInfo.objects, user__username=request.GET.get('name'))
    offices = user.exchange_offices.all()
    for office in offices:
        office.rates = office.rate_set.order_by('currency', '-buy')

    #rates = Rate.objects.filter(exchange_office__in=)
    return render(request, 'rates.html', {'offices': offices})




