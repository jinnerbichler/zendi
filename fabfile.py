import os
from fabric.api import run, env, task, cd, local
from fabric.context_managers import shell_env

env.use_ssh_config = True
env.hosts = ['iota_mail_1']


@task(default=True)
def deploy():
    # build docker image
    # local('npm install')
    # local('npm run build')
    # local('docker build -t jinnerbichler/zendi .')
    # local('docker push jinnerbichler/zendi')

    run('mkdir -p /srv/iota_mail/')
    with cd('/srv/iota_mail'):
        run('git pull origin master')
        with shell_env(XXX=os.getenv('EMAIL_HOST_PASSWORD')):
            run('echo "EMAIL_HOST_PASSWORD=$XXX" >> .env')
            run('docker-compose --project-name iota_mail up -d --force-recreate --no-deps iota_mail_web')



@task
def logs():
    with cd('/srv/iota_mail'):
        run('docker-compose --project-name iota_mail logs -f')


@task
def run_local():
    local('docker-compose --project-name iota_mail up --force-recreate')
