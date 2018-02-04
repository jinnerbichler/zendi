from fabric.api import run, env, task, put, cd

env.use_ssh_config = True
env.hosts = ['zendi_1']


@task(default=True)
def deploy():
    run('mkdir -p /srv/jenkins/')
    with cd('/srv/jenkins'):
        put('./[!jenkins_home]*', '.')  # all but volume
        run('docker-compose --project-name jenkins up -d --force-recreate')


@task
def logs():
    with cd('/srv/jenkins'):
        run('docker-compose logs -f')
