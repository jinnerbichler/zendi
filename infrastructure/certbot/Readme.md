# Deployment

## Certificate Creation

Created certificate can be found at ``/etc/letsencrypt/live/``.

## Certificate Renewal

A systemd timer service was setup to validate certificates once a day (randomly distributed over the day).
The proper files are placed at

```
/etc/systemd/system/certbot.service
/etc/systemd/system/certbot.service
```

and can also be found in this repository.

### Pre- and post hooks

Hooks were installed at ``/etc/letsencrypt/renewal-hooks/pre`` and ``/etc/letsencrypt/renewal-hooks/pre``, 
which starts and stops the nginx container before (and after) a certificate is renewed.

### Email notifications

The following packages where installed

```
sudo apt-get install ssmtp mailutils
```

and the following configuration added to ``/etc/ssmtp/ssmtp.conf``

```
Preconfiguring packages ...
#
# Config file for sSMTP sendmail
#
# The person who gets all mail for userids < 1000
# Make this empty to disable rewriting.
root=postmaster

# The place where the mail goes. The actual machine name is required no
# MX records are consulted. Commonly mailhosts are named mail.domain.com
mailhub=mail

# Where will the mail seem to come from?
#rewriteDomain=

# The full hostname
hostname=iota-mail-1

# Are users allowed to set their own From: address?
# YES - Allow the user to specify their own From: address
# NO - Use the system generated From: address

FromLineOverride=YES
AuthUser=zendimailer@gmail.com
AuthPass=Zendi2016
mailhub=smtp.gmail.com:587
UseSTARTTLS=YES
```

### Useful commands

* Initial setup

    ```
    systemctl daemon-reload
    systemctl start certbot.timer
    systemctl enable certbot.timer
    ```

* Check next execution

    ```
    systemctl list-timers certbot.timer
    ```
    
* Obtain log output

    ```
    journalctl -u certbot.timer
    journalctl -u certbot.service
    ```
