FROM python:3.6-onbuild
MAINTAINER Johannes Innerbichler <j.innerbichler@gmail.com>

ENV PYTHONPATH .
ENTRYPOINT ["python", "manage.py"]