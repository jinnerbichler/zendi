from fabric.api import task, local

# !set docker-machine to deployment VM first!

@task(default=True)
def deploy():
    # build docker image
    local('npm install')
    local('npm run build')

    local('docker-compose --project-name iota_mail up -d --build --force-recreate --no-deps iota_mail_web')
    local('docker-compose --project-name iota_mail logs -f iota_mail_web')


@task
def update_nginx():
    local('docker-compose --project-name iota_mail up -d --build --force-recreate --no-deps nginx')
    local('docker-compose --project-name iota_mail logs -f nginx')


@task
def logs():
    local('docker-compose --project-name iota_mail logs -f')


@task
def run_local():
    local('docker-compose --project-name iota_mail up --force-recreate')
