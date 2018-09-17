import logging

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


logger = logging.getLogger(__name__)


class AccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)

        if 'exchange_offices' in request.session:
            try:
                user.exchange_offices.add(*request.session.pop('exchange_offices'))
            except Exception:
                logger.exception("Wasn't able to pass session offices into db.")

        return user
