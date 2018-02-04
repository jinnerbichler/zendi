from zendi.settings import *

import os

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB_NAME', 'zendi_db'),
        'USER': os.getenv('POSTGRES_USER', 'root'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'changeme'),
        'HOST': os.getenv('POSTGRES_HOST', 'db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432')
    }
}

ALLOWED_HOSTS = ['*']

# Mailjets SMTP server
EMAIL_HOST = 'in-v3.mailjet.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'a2e5453485a3fd837b8dd5bf6192c1ea'
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'j.innerbichler@gmail.com'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

if not EMAIL_HOST_PASSWORD:
    raise Exception('Invalid config')
