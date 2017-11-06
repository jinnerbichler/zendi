import os
from fabric.api import run, env, task, cd, local

env.use_ssh_config = True
env.hosts = ['iota_mail_1']


@task(default=True)
def deploy():
    # build docker image
    local('npm install')
    local('npm run build')
    local('docker build -t jinnerbichler/zendi .')
    local('docker push jinnerbichler/zendi')

    with cd('/srv/iota_mail'):
        run('git pull origin master')

        # set proper secrets
        # run('echo "EMAIL_HOST_PASSWORD={}" > .env'.format(os.environ['EMAIL_HOST_PASSWORD']))
        run('docker-compose --project-name iota_mail up -d --force-recreate --no-deps iota_mail_web')


@task
def logs():
    with cd('/srv/iota_mail'):
        run('docker-compose --project-name iota_mail logs -f')


@task
def run_local():
    local('docker-compose --project-name iota_mail up --force-recreate')
