import logging
from urllib.parse import urlencode

from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods
from nopassword.utils import get_username_field
from rest_framework.status import HTTP_401_UNAUTHORIZED

from wallet.forms import SendTokensForm
from wallet.iota_ import NotEnoughBalanceException, iota_utils, iota_display_format
from wallet.templatetags.wallet_extras import iota_display_format_filter
from wallet.user_utils import get_user_safe

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

            # get user
            is_new, send_user = get_user_safe(email=form.cleaned_data['sender_mail'])

            # create login code
            login_code = authenticate(**{get_username_field(): send_user.username})
            login_code.next = exec_url
            login_code.save()

            # send login code
            logger.info('Sending login code to %s (new: %s)', send_user, is_new)
            login_code.send_login_code(secure=request.is_secure(),
                                       host=request.get_host(),
                                       new_user=is_new)

            user_message = 'Authentication email was sent to {}. ' \
                           'Please check you inbox.'.format(send_user.email)
            return JsonResponse(data={'message': user_message})
        else:
            return JsonResponse(data={'error': True, 'message': 'Invalid form data'})

    return redirect(index)


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
    user_message = render_to_string('wallet/messages/tokens_sent.txt', context)

    # compute redirect url
    response = custom_redirect(dashboard, user_message=user_message, message_type='info')

    # check if authorised user matches sending mail
    if sender_mail != request.user.email:
        return HttpResponse('Invalid mail', status=HTTP_401_UNAUTHORIZED)

    try:
        # send tokens
        iota_utils.send_tokens(sender=sender_mail, receiver=receiver_mail, value=amount, message=message)
    except NotEnoughBalanceException as e:
        response = custom_redirect(dashboard, user_message=str(e), message_type='error')

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


def logout_user(request):
    logout(request)
    return redirect('/')


def custom_redirect(view_name, **kwargs):
    return redirect('{}?{}'.format(reverse(view_name), urlencode(kwargs)))
