from fabric.api import run, env, task, put, cd, local

env.use_ssh_config = True
env.hosts = ['iota_mail_1']


@task(default=True)
def deploy():
    run('mkdir -p /srv/iota_mail/')
    with cd('/srv/iota_mail'):
        run('git pull origin master')
        run('docker-compose --project-name iota_mail up -d --force-recreate')


@task
def logs():
    with cd('/srv/iota_mail'):
        run('docker-compose logs -f')

@task
def run_local():
    local('docker-compose --project-name iota_mail up --force-recreate')