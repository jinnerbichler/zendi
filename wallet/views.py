from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from nopassword.utils import get_username_field
from urllib.parse import urlencode
from wallet.user_utils import get_user_safe
from django.shortcuts import render, redirect

from wallet.forms import SendForm


def index(request):
    form = SendForm()
    return render(request, 'wallet/index.html', {'form': form})


def send_coins_init(request):
    if request.method == 'POST':
        form = SendForm(request.POST)
        if form.is_valid():

            # check if user is already authenticatedx
            exec_url = '/send-coins-exec?{}'.format(urlencode(form.cleaned_data))
            if request.user.is_authenticated:
                return redirect(exec_url)

            # get user
            is_new, send_user = get_user_safe(email=form.cleaned_data['from_mail'])

            # create login code
            login_code = authenticate(**{get_username_field(): send_user.username})
            login_code.next = exec_url
            login_code.save()

            # send login code
            login_code.send_login_code(secure=request.is_secure(),
                                       host=request.get_host(),
                                       new_user=is_new)
        else:
            return render(request, 'wallet/index.html', {'form': form})

    return redirect('/')


@login_required
def send_coins_exec(request):
    logout(request)
    return redirect('/')
