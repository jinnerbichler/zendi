import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from nopassword.forms import AuthenticationForm
from rest_framework.status import HTTP_401_UNAUTHORIZED

from web import ClientRedirectResponse, client_redirect, paginate
from web.forms import SendTokensForm
from web.models import UserFeedback
from web.templatetags.wallet_extras import stellar_display_format_filter
from web.user_utils import send_login_mail, get_user_safe, send_token_received_email

from stellar import api as stellar

logger = logging.getLogger(__name__)

TRANSACTIONS_PER_PAGE = 5


@require_GET
def index(request):
    initial_values = {'sender_mail': request.user.email} if request.user.is_authenticated else {}
    if 'receiver' in request.GET:
        initial_values['receiver_mail'] = request.GET['receiver']
    if 'amount' in request.GET:
        initial_values['amount'] = request.GET['amount']
    form = SendTokensForm(initial=initial_values)
    return render(request, 'web/pages/landing.html', {'form': form, 'title': 'Send'})


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
        value = int(request.GET['amount'])
        context = {'amount_with_unit': stellar_display_format_filter(value=value), **request.GET}
        return render(request, 'web/pages/send-tokens-exec.html', context)

    elif request.method == 'POST':

        sender_mail = request.POST['sender_mail']
        receiver_mail = request.POST['receiver_mail']
        amount = float(request.POST['amount'])
        message = request.POST['message']  # optional

        # create message for user
        context = {'amount_with_unit': stellar_display_format_filter(value=amount), 'receiver': receiver_mail}
        user_message = render_to_string('web/messages/tokens_sent.txt', context=context)
        response = client_redirect(view=dashboard, replace=True,
                                   user_message=user_message, message_type='info')

        # check if authorised user matches sending mail
        if sender_mail != request.user.email:
            return HttpResponse('Invalid mail', status=HTTP_401_UNAUTHORIZED)
        try:
            #######################
            # sending tokens
            #######################
            _, sender = get_user_safe(email=sender_mail)
            is_new, receiver = get_user_safe(email=receiver_mail)

            logger.info('Transferring {} XLM from {} to {}'.format(amount, sender, receiver))
            stellar.transfer_lumen(sender=sender, to_address=receiver.stellaraccount.address, amount=amount)

            # inform receiver via mail
            send_token_received_email(request=request, sender=sender, receiver=receiver,
                                      is_new=is_new, amount=amount, message=message)

        except stellar.InsufficientBalanceException:
            user_message = render_to_string('web/messages/insufficient_balance.txt', context={})
            response = client_redirect(view=dashboard, replace=True,
                                       user_message=user_message, message_type='error')

        return response


@login_required
@require_http_methods(["GET", "POST"])
def withdraw(request):
    if request.method == 'GET':
        return render(request, 'web/pages/withdraw.html', {'title': 'Withdraw'})
    elif request.method == 'POST':
        sender = request.user
        address = request.POST['address']
        amount = request.POST['amount']

        logger.info('Withdrawing {} to {} (sender:{})'.format(amount, address, sender))
        try:
            stellar.transfer_lumen(sender=sender, to_address=address, amount=amount)
            return client_redirect(view=dashboard, replace=True,
                                   user_message='Withdrawal successful.', message_type='info')
        except Exception as ex:
            return JsonResponse(data={'error': True, 'message': str(ex)})


@login_required
@require_GET
def deposit(request):
    return render(request, 'web/pages/deposit.html', {'disabled': False, 'title': 'Deposit'})


@login_required
@require_GET
def deposit_address(request):
    generated_address = stellar.get_deposit_address(request.user)
    return JsonResponse(data={'address': generated_address})


@login_required
@require_GET
def dashboard(request):
    balance = stellar.get_balance(request.user, cached=True)
    transactions = stellar.get_transactions(request.user, cached=True)
    transactions = paginate(transactions, per_page=TRANSACTIONS_PER_PAGE, page=1)
    user_message = request.GET.get('user_message', default=None)
    message_type = request.GET.get('message_type', default=None)  # either 'info' or 'error'
    return render(request, 'web/pages/dashboard.html', {'logo_appendix': 'Dashboard',
                                                        'balance': balance,
                                                        'transactions': transactions,
                                                        'message': user_message,
                                                        'message_type': message_type,
                                                        'title': 'Dashboard'})


@login_required
@require_GET
def balance(request):
    balance = stellar.get_balance(request.user)
    return JsonResponse(data={'balance': balance, 'formatted': stellar_display_format_filter(balance)})


@login_required
@require_GET
def dashboard_transactions_ajax(request):
    page = request.GET.get('page', default=1)
    cached = request.GET.get('cached', default='false') == 'true'
    transactions = stellar.get_transactions(request.user, cached=cached)
    transactions = paginate(transactions, per_page=TRANSACTIONS_PER_PAGE, page=page)
    return render(request, 'web/components/transaction_list.html', {'transactions': transactions})


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
                                   template_name='web/pages/login.html')
    return login_view(request=request)


def logout(request):
    auth_logout(request)
    return redirect('/')


@csrf_exempt
@require_POST
def feedback(request):
    logger.info('Received feedback from {}'.format(request.user))

    sender = request.user if request.user.is_authenticated() else None
    message = request.POST['message']
    email = request.POST.get('email')
    UserFeedback.objects.create(sender=sender, message=message, email=email)

    return HttpResponse(status=204)


@require_GET
def send_external(request):
    return redirect('/')


def template_settings(request):
    return {
        'DEMO_MODE': settings.DEMO_MODE,
        'DEV_MODE': settings.DEV_MODE
    }
