from fabric.api import run, env, task, put, cd, local


@task(default=True)
def deploy():
    local('docker-compose pull')
    local('docker-compose --project-name iri up -d --force-recreate')


@task
def logs():
    local('docker-compose logs -f')
