from django.conf.urls import url
from wallet import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^send-tokens$', views.send_tokens_trigger, name='send_tokens'),
    url(r'^send-tokens-exec', views.send_tokens_exec, name='send_tokens_exec'),
    url(r'^withdraw', views.withdraw, name='withdraw'),
    url(r'^deposit', views.deposit, name='deposit'),
    url(r'^dashboard', views.dashboard, name='dashboard'),
    url(r'^logout', views.logout, name='logout'),
    url(r'^login', views.login, name='login'),
    url(r'^new_address', views.new_address, name='new_address')
]
