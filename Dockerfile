FROM python:3.6-onbuild
MAINTAINER Johannes Innerbichler <j.innerbichler@gmail.com>

# setup proper configuration
ENV PYTHONPATH .
ENV DJANGO_SETTINGS_MODULE iota_mail.settings-prod
ENV STATIC_ROOT /static

# collect static failed (e.g. can be be used by nginx)
RUN python manage.py collectstatic --noinput

ENTRYPOINT ["python", "manage.py"]