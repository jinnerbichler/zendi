from fabric.api import task, local


@task(default=True)
def deploy():
    # build docker image
    local('npm install')
    local('npm run build')

    local('docker-compose --project-name iota_mail up -d --build --force-recreate --no-deps iota_mail_web')


def update_nginx():
    local('docker-compose --project-name iota_mail up -d --build --force-recreate --no-deps nginx')


@task
def logs():
    local('docker-compose --project-name iota_mail logs -f')


@task
def run_local():
    local('docker-compose --project-name iota_mail up --force-recreate')
