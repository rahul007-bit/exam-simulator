# Solution for TR-022: Adjust Namespace CPU Quota to Prevent Throttling

## Summary
Deployment `data-sync` in `analytics` cannot create required replicas due to namespace CPU ResourceQuota. Increase quota or optimize pod requests.

## Commands
```bash
# Execute diagnosis and fixes for TR-022
kubectl -n analytics get all
```
