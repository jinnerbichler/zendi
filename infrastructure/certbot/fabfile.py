from fabric.api import run, env, task, put, cd, local

env.use_ssh_config = True
env.hosts = ['iota_mail_1']


@task(default=True)
def deploy():
    put('./pre_renewal.sh', '/etc/letsencrypt/renewal-hooks/pre/')
    put('./post_renewal.sh', '/etc/letsencrypt/renewal-hooks/post/')
