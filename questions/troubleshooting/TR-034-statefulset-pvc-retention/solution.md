# Solution for TR-034: Update StatefulSet PVC Retention Policy

## Summary
Configure StatefulSet `cache-node` in `stateful-db` with `persistentVolumeClaimRetentionPolicy` `whenDeleted: Delete`.

## Commands
```bash
# Execute diagnosis and fixes for TR-034
kubectl -n stateful-db get all
```
