# Solution for TR-020: Resolve Pod Anti-Affinity Scheduling Deadlock

## Summary
Deployment `web-redundant` in `web-tier` has 4 replicas but only 2 nodes exist with hard `podAntiAffinity`. Convert to soft affinity (`preferredDuringScheduling`).

## Commands
```bash
# Execute diagnosis and fixes for TR-020
kubectl -n web-tier get all
```
