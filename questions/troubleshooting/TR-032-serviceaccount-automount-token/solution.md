# Solution for TR-032: Enable automountServiceAccountToken on Pod

## Summary
Pod `api-client` in `order-auth` cannot contact Kubernetes API because `automountServiceAccountToken: false` is set. Enable token automounting.

## Commands
```bash
# Execute diagnosis and fixes for TR-032
kubectl -n order-auth get all
```
