import logging

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from nopassword.utils import get_username, get_username_field

import stellar_federation

logger = logging.getLogger(__name__)


def get_user_safe(email):
    """
    Gets a user object with the given mail.
    If no such user exists, a new one will be generated (including a new seed).
    """
    try:
        email = BaseUserManager.normalize_email(email=email)
        return False, User.objects.get(username=email)
    except User.DoesNotExist:
        pass

    user = User.objects.create_user(username=email, email=email, password='')
    return True, user


def login_url(code, secure=False, host=None):
    """
    :param code:
    :param secure:
    :param host:
    :return:
    """
    url_namespace = getattr(settings, 'NOPASSWORD_NAMESPACE', 'nopassword')
    username = get_username(code.user)
    host = host or getattr(settings, 'SERVER_URL', None) or 'example.com'
    if getattr(settings, 'NOPASSWORD_HIDE_USERNAME', False):
        view = reverse_lazy('{0}:login_with_code'.format(url_namespace),
                            args=[code.code]),
    else:
        view = reverse_lazy('{0}:login_with_code_and_username'.format(url_namespace),
                            args=[username, code.code]),

    return '%s://%s%s' % ('https' if secure else 'http', host, view[0])


def federation_callback(request, query, query_type):
    # check type of query
    if query_type != 'name':
        raise stellar_federation.NotImplementedException()

    # validate email
    email, domain = query.split('*')
    try:
        validate_email(email)
        email = BaseUserManager.normalize_email(email=email)
    except ValidationError:
        raise stellar_federation.NotFoundException('Address is not a valid email address')

    # check if handled by domain
    if domain != request.get_host():
        raise stellar_federation.NotFoundException('Invalid host name')

    # get or create user
    new_user, user = get_user_safe(email)

    # build response
    response = {
        "stellar_address": query,
        "account_id": user.stellaraccount.address,
    }

    if new_user:
        logger.info('(Federation) Created user {} from federation request (q={}, type={})'.format(user, query,
                                                                                                  query_type))
        send_federation_account_created(request=request, user=user)
        response['memo_type'] = 'text'
        response['memo'] = 'new account created'

    logger.info('(Federation) Returning account {} ({})'.format(user.stellaraccount.address, user))

    return response


def send_login_mail(request, next_url, email):
    # get user
    is_new, send_user = get_user_safe(email=email)

    # create login code
    login_code = authenticate(**{get_username_field(): send_user.username})
    login_code.next = next_url
    login_code.save()

    # send login code
    logger.info('Sending login code to %s (new: %s)', send_user, is_new)
    login_code.send_login_code(secure=request.is_secure(), host=request.get_host())

    return render_to_string('web/messages/login_sent.txt', context={'mail': send_user.email})


def send_federation_account_created(request, user):
    # create login code
    login_code = authenticate(**{get_username_field(): user.username})
    login_code.next = '/dashboard'
    login_code.save()

    # generate email body
    url_for_login = login_url(code=login_code, secure=request.is_secure(), host=request.get_host())
    context = {
        'login_url': url_for_login,
        'email': user.email,
        'domain': request.get_host()
    }
    text_content = render_to_string('web/emails/federation_account_created.txt', context)

    # send mail
    to_email = [user.email]
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'root@example.com')
    subject = 'Welcome to Zėndi'
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.send()

    logger.info('(Federation) Sent welcome mail to %s (federation)', user)


def send_token_received_email(request, sender, receiver, amount, is_new, message):
    # create login code
    login_code = authenticate(**{get_username_field(): receiver.username})
    login_code.next = '/dashboard'
    login_code.save()

    # generate email body
    url_for_login = login_url(code=login_code, secure=request.is_secure(), host=request.get_host())
    context = {'login_url': url_for_login,
               'code': login_code,
               'from_email': sender.email,
               'is_new': is_new,
               # 'amount': iota_display_format_filter(amount),
               'amount': amount,
               'message': message}
    text_content = render_to_string('web/emails/tokens_received.txt', context)
    # html_content = render_to_string('wallet/email/login_email.html', context)

    # send mail
    to_email = [receiver.email]
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'root@example.com')
    subject = 'Welcome to Zėndi' if is_new else 'Payment received from {}'.format(sender.email)
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    # msg.attach_alternative(html_content, 'text/html')
    msg.send()

    logger.info('Sent payment received mail to %s (new: %s)', receiver, is_new)
