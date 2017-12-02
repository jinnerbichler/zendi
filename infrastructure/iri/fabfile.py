from fabric.api import run, env, task, put, cd, local, sudo

env.use_ssh_config = True
env.hosts = ['iota_mail_1']


@task(default=True)
def deploy():
    run('mkdir -p /srv/iri/')
    with cd('/srv/iri'):
        put('.', '.')
        run('docker-compose --project-name iri pull')
        run('docker-compose --project-name iri up -d --force-recreate')


@task
def deploy_vm():
    with cd('/data/misc/'):
        put('.', '.')
        sudo('docker-compose -f docker-compose-vm.yml pull')
        sudo('docker-compose -f docker-compose-vm.yml up -d --force-recreate')


@task
def logs():
    with cd('/srv/iri'):
        run('docker-compose logs -f')


@task
def run_local():
    local('docker-compose --project-name iri up -d --force-recreate')
