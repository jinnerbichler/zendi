import logging
from urllib.parse import urlencode

from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_http_methods
from nopassword.forms import AuthenticationForm
from nopassword.models import LoginCode
from nopassword.utils import get_username_field
from rest_framework.status import HTTP_401_UNAUTHORIZED

from wallet import custom_redirect
from wallet.forms import SendTokensForm
from wallet.iota_ import InsufficientBalanceException, iota_utils
from wallet.templatetags.wallet_extras import iota_display_format_filter
from wallet.user_utils import send_login_mail

logger = logging.getLogger(__name__)


class ClientRedirectResponse(JsonResponse):
    def __init__(self, redirect_url, **kwargs):
        super().__init__(data={'redirect_url': redirect_url}, **kwargs)


@require_GET
def index(request):
    initial_values = {'sender_mail': request.user.email} if request.user.is_authenticated else {}
    form = SendTokensForm(initial=initial_values)
    return render(request, 'wallet/index.html', {'form': form})


@require_http_methods(["GET", "POST"])
def send_tokens_trigger(request):
    if request.method == 'POST':
        form = SendTokensForm(request.POST)
        if form.is_valid():

            # check if user is already authenticated
            exec_url = '/send-tokens-exec?{}'.format(urlencode(form.cleaned_data))
            if request.user.is_authenticated:
                return ClientRedirectResponse(redirect_url=exec_url)

            email = form.cleaned_data['sender_mail']
            user_message = send_login_mail(request=request, next_url=exec_url, email=email)
            return JsonResponse(data={'message': user_message})
        else:
            return JsonResponse(data={'error': True, 'message': 'Invalid form data'})

    return redirect(index)


@login_required
@require_GET
def withdraw(request):
    return render(request, 'wallet/withdraw.html')


@login_required
@require_GET
def deposit(request):
    return render(request, 'wallet/deposit.html')


@login_required
@require_http_methods(["GET", " POST"])
def send_tokens_exec(request):
    sender_mail = request.GET['sender_mail']
    receiver_mail = request.GET['receiver_mail']
    amount = int(request.GET['amount'])
    message = request.GET['message']  # optional

    # all computations should be performed before communicating with the Tangle.

    # create message for user
    context = {'amount_with_unit': iota_display_format_filter(amount), 'receiver': receiver_mail}
    user_message = render_to_string('wallet/messages/tokens_sent.txt', context=context)

    # compute redirect url
    response = custom_redirect(view=dashboard, user_message=user_message, message_type='info')

    # check if authorised user matches sending mail
    if sender_mail != request.user.email:
        return HttpResponse('Invalid mail', status=HTTP_401_UNAUTHORIZED)

    try:
        # send tokens
        iota_utils.send_tokens(sender=sender_mail, receiver=receiver_mail, value=amount, message=message)
    except InsufficientBalanceException:
        user_message = render_to_string('wallet/messages/insufficient_balance.txt', context={})
        response = custom_redirect(view=dashboard, user_message=user_message, message_type='error')

    return response


@login_required
@require_GET
def dashboard(request):
    # balance, transactions = iota_utils.get_account_data(request.user)
    balance, transactions = (0.0, [])
    user_message = request.GET.get('user_message', default=None)
    message_type = request.GET.get('message_type', default=None)  # either 'info' or 'error'
    return render(request, 'wallet/dashboard.html', {'logo_appendix': 'Dashboard',
                                                     'balance': balance,
                                                     'transactions': transactions[:4],  # last 4 transactions
                                                     'message': user_message,
                                                     'message_type': message_type})


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user_message = send_login_mail(request=request,
                                           next_url=request.GET.get('next'),
                                           email=request.POST.get('username'))
            return JsonResponse(data={'message': user_message})
        else:
            return JsonResponse(data={'error': True, 'message': 'Invalid form data'})

    login_view = LoginView.as_view(authentication_form=AuthenticationForm,
                                   template_name='wallet/login.html')
    return login_view(request=request)


def logout(request):
    auth_logout(request)
    return redirect('/')
