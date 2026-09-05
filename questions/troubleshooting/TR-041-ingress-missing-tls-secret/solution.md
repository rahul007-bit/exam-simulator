# Solution for TR-041: Create Missing TLS Secret for Ingress HTTPS

## Summary
Ingress `secure-web` in `tls-ingress` references missing Secret `web-tls-cert`. Create TLS secret `web-tls-cert`.

## Commands
```bash
# Execute diagnosis and fixes for TR-041
kubectl -n tls-ingress get all
```
