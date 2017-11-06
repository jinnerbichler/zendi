from fabric.api import task, local


@task(default=True)
def deploy():
    # build docker image
    local('npm install')
    local('npm run build')
    # local('docker build -t jinnerbichler/zendi .')
    # local('docker push jinnerbichler/zendi')

    local('docker-compose --project-name iota_mail up -d --build --force-recreate --no-deps iota_mail_web')


@task
def logs():
    local('docker-compose --project-name iota_mail logs -f')


@task
def run_local():
    local('docker-compose --project-name iota_mail up --force-recreate')
