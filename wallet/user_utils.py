from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from nopassword.utils import get_username


def get_user_safe(email):
    try:
        return False, User.objects.get(username=email)
    except User.DoesNotExist:
        pass

    user = User.objects.create_user(username=email, email=email, password='')

    # ToDo create seed and store in object

    return True, user


def login_url(code, secure=False, host=None):
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
