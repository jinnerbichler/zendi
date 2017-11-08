import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from nopassword.utils import get_username, get_username_field

from wallet.templatetags.wallet_extras import iota_display_format_filter

logger = logging.getLogger(__name__)


def get_user_safe(email):
    """
    Gets a user object with the given mail.
    If no such user exists, a new one will be generated (including a new seed).
    """
    try:
        return False, User.objects.get(username=email)
    except User.DoesNotExist:
        pass

    user = User.objects.create_user(username=email, email=email, password='')
    # ToDo Maybe send invitation mail
    return True, user


def login_url(code, secure=False, host=None):
    # ToDo comment
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

    return render_to_string('wallet/messages/login_sent.txt', context={'mail': send_user.email})


def send_token_received_email(request, sender, receiver, amount, is_new, message):
    # create login code
    login_code = authenticate(**{get_username_field(): receiver.username})
    login_code.next = '/dashboard'
    login_code.save()

    to_email = [receiver.email]
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'root@example.com')

    # generate email body
    url_for_login = login_url(code=login_code, secure=request.is_secure(), host=request.get_host())
    context = {'login_url': url_for_login,
               'code': login_code,
               'from_email': sender.email,
               'is_new': is_new,
               'amount': iota_display_format_filter(amount),
               'message': message}
    text_content = render_to_string('wallet/emails/tokens_received.txt', context)
    # html_content = render_to_string('wallet/email/login_email.html', context)

    # send mail
    subject = 'Welcome to Zėndi' if is_new else 'Payment received from {}'.format(sender.email)
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    # msg.attach_alternative(html_content, 'text/html')
    msg.send()

    logger.info('Sent payment received mail to %s (new: %s)', receiver, is_new)
