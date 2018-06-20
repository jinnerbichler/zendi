# Zendi

Zėndi provides Stellar Lumen accounts to everyone who has a working email address. It even allows people to exchange Lumens between emails, whereas accounts are created automatically if the email of the recipient not yet linked to an account.
The idea behind Zėndi is to be as simple and minimalistic as possible. You don't even need a password. Every authentication is done in a passwordless manner.

Clone with `git clone --recursive https://github.com/jinnerbichler/zendi` in order to include submodules.

## Execution

Run with

```
python manage.py runserver
```

in order to start Zendi locally.

## Docker

The file `docker-compose.yml` sets up a composition of necessary services (e.g. Postgre database), which can be used for local development.

Run

```
docker-compose up
```

for building the application and start necessary services via Docker.

**Depencencies**:


* **Python**: Version 3.5
* **Docker**: Version 18.03.0-ce
* **Docker-compose**: Version 1.20
