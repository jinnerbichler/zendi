import logging
from urllib.parse import urlencode

from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods
from nopassword.forms import AuthenticationForm
from rest_framework.status import HTTP_401_UNAUTHORIZED

from wallet import ClientRedirectResponse, client_redirect
from wallet.forms import SendTokensForm
from wallet.iota_ import InsufficientBalanceException, iota_utils, normalize_value
from wallet.models import IotaBalance
from wallet.templatetags.wallet_extras import iota_display_format_filter
from wallet.user_utils import send_login_mail, get_user_safe

logger = logging.getLogger(__name__)


@require_GET
def index(request):
    initial_values = {'sender_mail': request.user.email} if request.user.is_authenticated else {}
    form = SendTokensForm(initial=initial_values)
    return render(request, 'wallet/pages/landing.html', {'form': form})


@require_http_methods(["GET", "POST"])
def send_tokens_trigger(request):
    if request.method == 'POST':
        form = SendTokensForm(request.POST)
        if form.is_valid():

            receiver_mail = form.cleaned_data['receiver_mail']
            if request.user.is_authenticated and receiver_mail == request.user.email:
                return JsonResponse(data={'error': True, 'message': 'Cannot send to yourself'})

            # check if user is already authenticated
            exec_url = '/send-tokens-exec?{}'.format(urlencode(form.cleaned_data))
            if request.user.is_authenticated:
                return ClientRedirectResponse(redirect_url=exec_url)

            sender_mail = form.cleaned_data['sender_mail']
            user_message = send_login_mail(request=request, next_url=exec_url, email=sender_mail)
            return JsonResponse(data={'message': user_message})
        else:
            return JsonResponse(data={'error': True, 'message': 'Invalid data'})

    return redirect(index)


@csrf_exempt  # this calls are executed manually
@login_required
@require_http_methods(["GET", "POST"])
def send_tokens_exec(request):
    if request.method == 'GET':
        value = normalize_value(value=int(request.GET['amount']), unit=request.GET['unit'])
        context = {'amount_with_unit': iota_display_format_filter(value=value), **request.GET}
        return render(request, 'wallet/pages/send-tokens-exec.html', context)

    elif request.method == 'POST':

        sender_mail = request.POST['sender_mail']
        receiver_mail = request.POST['receiver_mail']
        amount = int(request.POST['amount'])
        unit = request.POST['unit']
        message = request.POST['message']  # optional

        # all computations should be performed before communicating with the Tangle.

        # create message for user
        value = normalize_value(value=amount, unit=unit)
        context = {'amount_with_unit': iota_display_format_filter(value=value), 'receiver': receiver_mail}
        user_message = render_to_string('wallet/messages/tokens_sent.txt', context=context)
        response = client_redirect(view=dashboard, replace=True,
                                   user_message=user_message, message_type='info')

        # check if authorised user matches sending mail
        if sender_mail != request.user.email:
            return HttpResponse('Invalid mail', status=HTTP_401_UNAUTHORIZED)
        try:
            #############
            # sending tokens
            #############
            iota_utils.send_tokens(request=request, sender_mail=sender_mail, receiver_mail=receiver_mail,
                                   value=value, message=message)
        except InsufficientBalanceException:
            user_message = render_to_string('wallet/messages/insufficient_balance.txt', context={})
            response = client_redirect(view=dashboard, replace=True,
                                       user_message=user_message, message_type='error')

        return response


@login_required
@require_GET
def withdraw(request):
    return render(request, 'wallet/pages/withdraw.html')


@login_required
@require_GET
def deposit(request):
    return render(request, 'wallet/pages/deposit.html')


@login_required
@require_GET
def new_address(request):
    generated_address = iota_utils.get_new_address(request.user, with_checksum=True)
    return JsonResponse(data={'address': generated_address})


@login_required
@require_GET
def dashboard(request):
    balance = IotaBalance.objects.get_or_create(user=request.user)[0].balance
    transactions = iota_utils.get_cached_transactions(request.user)[:4]
    user_message = request.GET.get('user_message', default=None)
    message_type = request.GET.get('message_type', default=None)  # either 'info' or 'error'
    return render(request, 'wallet/pages/dashboard.html', {'logo_appendix': 'Dashboard',
                                                           'balance': balance,
                                                           'transactions': transactions,
                                                           'message': user_message,
                                                           'message_type': message_type})


@login_required
@require_GET
def balance(request):
    balance = iota_utils.get_balance(request.user)
    return JsonResponse(data={'balance': balance, 'formatted': iota_display_format_filter(balance)})


@login_required
@require_GET
def dashboard_transactions_ajax(request):
    transactions = iota_utils.get_account_data(request.user)
    return render(request, 'wallet/components/transaction_list.html', {'transactions': transactions[:6]})


def login(request):
    if request.method == 'POST':

        # create new user if necessary
        get_user_safe(email=request.POST['username'])

        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            next_url = request.GET.get('next', default='/dashboard')
            user_message = send_login_mail(request=request, next_url=next_url, email=request.POST['username'])
            return JsonResponse(data={'message': user_message})
        else:
            return JsonResponse(data={'error': True, 'message': 'Invalid form data'})

    login_view = LoginView.as_view(authentication_form=AuthenticationForm,
                                   template_name='wallet/pages/login.html')
    return login_view(request=request)


def logout(request):
    auth_logout(request)
    return redirect('/')
