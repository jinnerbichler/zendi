from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

from wallet.forms import SendForm


def index(request):
    form = SendForm()
    return render(request, 'wallet/index.html', {'form': form})


def send_coins(request):
    if request.method == 'POST':
        form = SendForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/thanks/')

    return redirect('/')
