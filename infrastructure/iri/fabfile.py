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
        put('./docker-compose-vm.yml', '.')
        put('iota.ini', '.')
        put('logback.xml', '.')
        sudo('docker-compose -f docker-compose-vm.yml pull')
        sudo('docker-compose -f docker-compose-vm.yml up -d --force-recreate')


@task
def stop():
    with cd('/srv/iri'):
        run('docker-compose --project-name iri stop')


@task
def logs_tail():
    with cd('/srv/iri'):
        run('docker-compose logs -f --tail 100')


@task
def logs_all():
    with cd('/srv/iri'):
        run('docker-compose logs -f')


@task
def run_local():
    local('docker-compose --project-name iri up -d --force-recreate')
