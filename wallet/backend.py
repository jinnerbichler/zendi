# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from nopassword.backends.base import NoPasswordBackend

from wallet.user_utils import login_url


class EmailBackend(NoPasswordBackend):
    def send_login_code(self, code, secure=False, host=None, **kwargs):
        subject = getattr(settings, 'NOPASSWORD_LOGIN_EMAIL_SUBJECT', _('Login code'))
        to_email = [code.user.email]
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'root@example.com')

        context = {'url': login_url(code=code, secure=secure, host=host), 'code': code}
        text_content = render_to_string('registration/login_email.txt', context)
        html_content = render_to_string('registration/login_email.html', context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
