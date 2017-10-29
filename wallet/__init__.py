from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse


def custom_redirect(view, **kwargs):
    return redirect('{}?{}'.format(reverse(view), urlencode(kwargs)))
