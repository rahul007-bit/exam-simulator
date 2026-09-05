# Solution for TR-014: Clear Leftover NoSchedule Cordon on Node

## Summary
Node is cordoned. Uncordon so deployment `worker-pool` in `prod-workers` scales to 3 replicas.

## Commands
```bash
# Execute diagnosis and fixes for TR-014
kubectl -n prod-workers get all
```
