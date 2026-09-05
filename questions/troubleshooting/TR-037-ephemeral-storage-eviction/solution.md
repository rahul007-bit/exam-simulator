# Solution for TR-037: Set Ephemeral Storage Request and Limit on Worker Pod

## Summary
Pod `log-cruncher` in `log-aggregator` is evicted due to exceeding ephemeral storage. Add `ephemeral-storage: 500Mi` request and limit.

## Commands
```bash
# Execute diagnosis and fixes for TR-037
kubectl -n log-aggregator get all
```
