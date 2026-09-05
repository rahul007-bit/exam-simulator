# Solution for TR-017: Resolve PVC ReadWriteMany on ReadWriteOnce Storage

## Summary
PVC `shared-data` in `media-platform` fails to bind because accessMode `ReadWriteMany` is unsupported on local disk.

## Commands
```bash
# Execute diagnosis and fixes for TR-017
kubectl -n media-platform get all
```
