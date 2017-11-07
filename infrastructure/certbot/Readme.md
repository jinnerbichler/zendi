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
