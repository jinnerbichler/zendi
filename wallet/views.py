from django.contrib.auth import authenticate
from nopassword.utils import get_username_field

from wallet.user_utils import get_user_safe
from django.shortcuts import render, redirect
import nopassword

from wallet.forms import SendForm


def index(request):
    form = SendForm()
    return render(request, 'wallet/index.html', {'form': form})


def send_coins(request):
    if request.method == 'POST':
        form = SendForm(request.POST)
        if form.is_valid():

            is_new, send_user = get_user_safe(email=form.cleaned_data['from_mail'])

            user_cache = authenticate(**{get_username_field(): send_user.username})

            print(user_cache)


        else:
            return render(request, 'wallet/index.html', {'form': form})

    return redirect('/')
