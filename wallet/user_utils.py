from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from nopassword.utils import get_username

from wallet.api.iota_api import IotaApi
from wallet.models import IotaAddress


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
    return True, user


# noinspection PyUnresolvedReferences
def get_new_address(user):
    """
    Creates a new IOTA address, which is not attached to the tangle.
    :param user: user object containing seed
    :return: new address in the IOTA network (not attached to the Tangle)
    """
    api = IotaApi(seed=user.iota_seed)

    # create and store new address
    new_address = api.get_new_address()
    IotaAddress.objects.get_or_create(user=user, address=new_address)

    return new_address


def send_iota(sender, receiver, amount, message):
    # get proper users
    _, sending_user = get_user_safe(email=sender)
    is_new, receiving_user = get_user_safe(email=receiver)

    # ToDo: inform user about new wallet

    api = IotaApi(seed=sending_user.iotaseed.seed)

    return


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
