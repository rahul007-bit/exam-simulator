# Solution for TR-031: Fix InitContainer Log Directory Creation Race

## Summary
Container `logger` crashes because directory `/var/log/app` in shared volume is not yet initialized by `app`. Add initContainer to ensure path exists.

## Commands
```bash
# Execute diagnosis and fixes for TR-031
kubectl -n log-collector get all
```
