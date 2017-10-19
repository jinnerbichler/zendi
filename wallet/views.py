import logging

from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from nopassword.utils import get_username_field
from urllib.parse import urlencode

from rest_framework.status import HTTP_401_UNAUTHORIZED

import wallet.iota_.iota_utils as iota_utils
from wallet.iota_ import NotEnoughBalanceException
from wallet.user_utils import get_user_safe
from django.shortcuts import render, redirect

from wallet.forms import SendForm

logger = logging.getLogger(__name__)


def index(request):
    form = SendForm()
    return render(request, 'wallet/index.html', {'form': form})


def send_tokens_init(request):
    if request.method == 'POST':
        form = SendForm(request.POST)
        if form.is_valid():

            # check if user is already authenticated
            exec_url = '/send-tokens-exec?{}'.format(urlencode(form.cleaned_data))
            if request.user.is_authenticated:
                return redirect(exec_url)

            # get user
            is_new, send_user = get_user_safe(email=form.cleaned_data['from_mail'])

            # create login code
            login_code = authenticate(**{get_username_field(): send_user.username})
            login_code.next = exec_url
            login_code.save()

            # send login code
            logger.info('Sending login code to %s (new: %s)', send_user, is_new)
            login_code.send_login_code(secure=request.is_secure(),
                                       host=request.get_host(),
                                       new_user=is_new)
        else:
            return render(request, 'wallet/index.html', {'form': form})

    return redirect('/')


@login_required
def send_tokens_exec(request):
    from_mail = request.GET['from_mail']
    to_mail = request.GET['to_mail']
    amount = int(request.GET['amount'])
    message = request.GET['message']  # optional

    # check if authorised user matches sending mail
    if from_mail != request.user.email:
        return HttpResponse('Invalid mail', status=HTTP_401_UNAUTHORIZED)

    try:
        # send tokens
        iota_utils.send_tokens(sender=from_mail, receiver=to_mail, amount=amount, msg=message)
    except NotEnoughBalanceException as e:
        # ToDo: handle this case
        pass

    logout(request)
    return redirect('/')
