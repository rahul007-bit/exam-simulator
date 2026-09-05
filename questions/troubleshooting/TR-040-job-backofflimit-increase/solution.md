# Solution for TR-040: Increase Batch Job backoffLimit and Fix Failing Command

## Summary
Job `batch-sync` in `data-import` failed 6 times and hit `backoffLimit`. Increase backoffLimit to `10` and fix command typo so job completes.

## Commands
```bash
# Execute diagnosis and fixes for TR-040
kubectl -n data-import get all
```
