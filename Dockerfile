FROM python:3.5-onbuild
MAINTAINER Johannes Innerbichler <j.innerbichler@gmail.com>

EXPOSE 8000
ENV PYTHONPATH .
ENTRYPOINT ["python", "manage.py"]