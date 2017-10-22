import logging
from urllib.parse import urlencode

from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from nopassword.utils import get_username_field
from rest_framework.status import HTTP_401_UNAUTHORIZED

from wallet.forms import SendTokensForm
from wallet.iota_ import NotEnoughBalanceException, iota_utils
from wallet.iota_.iota_utils import send_tokens
from wallet.user_utils import get_user_safe

logger = logging.getLogger(__name__)


class ClientRedirectResponse(JsonResponse):
    def __init__(self, redirect_url, **kwargs):
        super().__init__(data={'redirect_url': redirect_url}, **kwargs)


def index(request):
    initial_values = {'sender_mail': request.user.email} if request.user.is_authenticated else {}
    form = SendTokensForm(initial=initial_values)
    return render(request, 'wallet/index.html', {'form': form})


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
def send_tokens_exec(request):
    sender_mail = request.GET['sender_mail']
    receiver_mail = request.GET['receiver_mail']
    amount = int(request.GET['amount'])
    message = request.GET['message']  # optional

    # check if authorised user matches sending mail
    if sender_mail != request.user.email:
        return HttpResponse('Invalid mail', status=HTTP_401_UNAUTHORIZED)

    try:
        # send tokens
        bundle = send_tokens(sender=sender_mail, receiver=receiver_mail, amount=amount, msg=message)

        print(bundle)

    except NotEnoughBalanceException as e:
        # ToDo: handle this case
        pass

    # ToDo: display proper message in message box
    return redirect(dashboard)


@login_required
def dashboard(request):
    return render(request, 'wallet/dashboard.html', {'logo_appendix': 'Dashboard'})


def logout_user(request):
    logout(request)
    return redirect('/')
