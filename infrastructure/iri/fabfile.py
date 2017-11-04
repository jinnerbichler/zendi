from fabric.api import run, env, task, put, cd, local

env.use_ssh_config = True
env.hosts = ['iota_mail_1']


@task(default=True)
def deploy():
    with cd('/srv/iri'):
        put('.', '.')
        run('docker-compose pull')
        run('docker-compose --project-name iri up -d --force-recreate')


@task
def logs():
    with cd('/srv/iri'):
        run('docker-compose logs -f')


@task
def run_local():
    local('docker-compose --project-name iri up -d --force-recreate')
