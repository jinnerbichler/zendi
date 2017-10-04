from django.conf.urls import url
from wallet import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^send-coins/$', views.send_coins, name='send_coin')
]
