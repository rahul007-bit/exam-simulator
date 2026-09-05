# Solution for SC-005: Create TLS Secret and Mount into Nginx Pod

In namespace `secure-ingress`, create a TLS secret `app-tls-secret` (cert/key) and mount into pod `tls-web` at `/etc/tls`.
