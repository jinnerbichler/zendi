# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import FieldError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import make_aware
from nopassword.backends.base import NoPasswordBackend
from nopassword.models import LoginCode
from nopassword.utils import get_user_model

from wallet.user_utils import login_url

logger = logging.getLogger(__name__)


class EmailBackend(NoPasswordBackend):
    def send_login_code(self, code, secure=False, host=None, **kwargs):
        to_email = [code.user.email]
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'root@example.com')

        context = {'url': login_url(code=code, secure=secure, host=host), 'code': code}
        text_content = render_to_string('wallet/emails/login_email.txt', context)
        # html_content = render_to_string('wallet/email/login_email.html', context)

        msg = EmailMultiAlternatives('Zėndi Login', text_content, from_email, to_email)
        # msg.attach_alternative(html_content, 'text/html')
        msg.send()

    def authenticate(self, request=None, code=None, **credentials):
        try:
            user = get_user_model().objects.get(**credentials)
            if not self.verify_user(user):
                return None
            if code is None:
                return LoginCode.create_code_for_user(user)
            else:
                logger.info('Login in user %s', user)
                timeout = getattr(settings, 'NOPASSWORD_LOGIN_CODE_TIMEOUT', 900)
                timestamp = make_aware(datetime.now() - timedelta(seconds=timeout))
                login_code = LoginCode.objects.get(user=user, code=code, timestamp__gt=timestamp)
                user = login_code.user
                user.code = login_code
                login_code.delete()
                return user
        except (TypeError, get_user_model().DoesNotExist, LoginCode.DoesNotExist, FieldError):
            return None
