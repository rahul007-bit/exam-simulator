# Solution for TR-C04: Chaos: Untangle Triple-Constraint NodeAffinity and Taint Knot

## Summary
5 pods in `compute-pool` are deadlocked due to circular nodeAffinity, zone taints, and podAntiAffinity. Resolve constraints so all 5 pods schedule.

## Commands
```bash
# Execute diagnosis and fixes for TR-C04
kubectl -n compute-pool get all
```
