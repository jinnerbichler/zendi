from django.conf.urls import url
from wallet import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^send-coins/$', views.send_coins_init, name='send_coin'),
    url(r'^send-coins-exec', views.send_coins_exec, name='send_coin_exec')
]
