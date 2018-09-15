import logging

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db.transaction import atomic
from django.db.utils import IntegrityError


from exchange.models import UserInfo
from exchange.utils.deprecated import get_username


logger = logging.getLogger(__name__)


def cookie_to_session_auth_middleware(get_response):
    """
    This middleware should go after default auth middleware.
    It authenticates legacy users with a cookie encoded name.
    """

    def process_request(request):
        auth_by_cookie(request)
        return get_response(request)

    return process_request


@atomic
def auth_by_cookie(request):
    if request.user.is_authenticated:
        return

    deprecated_name = get_username(request)

    if deprecated_name is None:
        return

    deprecated_user = UserInfo.objects.filter(name=deprecated_name).first()

    if deprecated_user is None:
        return

    try:
        user = User.objects.create(username=deprecated_name)
    except IntegrityError:
        logger.exception("Failed to create user %s", deprecated_name)
        return

    logger.info('Successfully created user %s', user.username)

    user.exchange_offices.set(deprecated_user.exchange_offices.all())
    deprecated_user.delete()

    login(request, user)

    logger.info('Successfully duplicated user %s info', user.username)

    return
