from urllib.parse import urlencode

from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


class ClientRedirectResponse(JsonResponse):
    def __init__(self, redirect_url, **kwargs):
        super().__init__(data={'redirect_url': redirect_url}, **kwargs)


def custom_uri(view, **kwargs):
    return '{}?{}'.format(reverse(view), urlencode(kwargs))


def server_redirect(view, **kwargs):
    return redirect(custom_uri(view=view, **kwargs))


def client_redirect(view, **kwargs):
    return ClientRedirectResponse(redirect_url=custom_uri(view=view, **kwargs))
