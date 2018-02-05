from django.conf.urls import url
from web import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^send-tokens$', views.send_tokens_trigger, name='send_tokens'),
    url(r'^send-tokens-exec', views.send_tokens_exec, name='send_tokens_exec'),
    url(r'^withdraw', views.withdraw, name='withdraw'),
    url(r'^deposit', views.deposit, name='deposit'),
    url(r'^dashboard_transactions_ajax', views.dashboard_transactions_ajax, name='dashboard_transactions'),
    url(r'^dashboard', views.dashboard, name='dashboard'),
    url(r'^balance', views.balance, name='balance'),
    url(r'^logout', views.logout, name='logout'),
    url(r'^login', views.login, name='login'),
    url(r'^new_address', views.deposit_address, name='new_address')
]
