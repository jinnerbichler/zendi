FROM python:3.6-onbuild
MAINTAINER Johannes Innerbichler <j.innerbichler@gmail.com>

# setup proper configuration
ENV PYTHONPATH .
ENV DJANGO_SETTINGS_MODULE iota_mail.settings-prod
ENV STATIC_ROOT /static

ENTRYPOINT ["python", "manage.py"]