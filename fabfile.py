from fabric.api import task, local


##############################################
# !set docker-machine to deployment VM first!
#############################################


@task(default=True)
def deploy():
    # build docker image
    local('npm install')
    local('npm run build')

    local('docker-compose --project-name zendi up -d --build --force-recreate --no-deps zendi_web')
    local('docker-compose --project-name zendi logs -f zendi_web')


@task
def update_nginx():
    local('docker-compose --project-name zendi up -d --build --force-recreate --no-deps nginx')
    local('docker-compose --project-name zendi logs -f nginx')


@task
def init():
    # local('docker network create nginx-backend')
    local('docker-compose --project-name zendi up -d --build --force-recreate')


@task
def logs():
    local('docker-compose --project-name zendi logs -f')

@task
def logs_web():
    local('docker-compose --project-name zendi logs -f zendi_web')


@task
def run_local():
    local('docker-compose --project-name zendi up --force-recreate')
