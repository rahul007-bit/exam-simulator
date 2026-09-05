# Solution for ST-008: Mount Secret and ConfigMap as File Volumes in Specific Paths

Create Pod `config-reader` in `app-configs` mounting Secret `app-secret` at `/etc/secrets/token` and ConfigMap `app-config` at `/etc/config/app.conf`.
