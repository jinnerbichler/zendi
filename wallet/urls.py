from django.conf.urls import url
from wallet import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^send-tokens/$', views.send_tokens_init, name='send_tokens'),
    url(r'^send-tokens-exec', views.send_tokens_exec, name='send_tokens_exec')
]
