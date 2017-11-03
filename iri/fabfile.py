from fabric.api import local, run, env, task, hide, put, cd

env.use_ssh_config = True
env.hosts = ['iota_mail_1']


@task(default=True)
def deploy():
    with cd('/srv/iri'):
        put('.', '.')
        run('docker-compose pull')
        run('docker-compose up -d --force-recreate')


@task
def logs():
    with cd('/srv/iri'):
        run('docker-compose logs -f')
