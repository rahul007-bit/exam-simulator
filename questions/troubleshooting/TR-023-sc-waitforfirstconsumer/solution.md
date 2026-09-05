# Solution for TR-023: Add WaitForFirstConsumer to Local StorageClass

## Summary
Local PV cannot bind to PVC because StorageClass lacks `volumeBindingMode: WaitForFirstConsumer`. Update StorageClass.

## Commands
```bash
# Execute diagnosis and fixes for TR-023
kubectl -n data-nodes get all
```
