# Solution for TR-029: Fix PodDisruptionBudget minAvailable 100% Blocking Drain

## Summary
PDB `strict-pdb` in `payment-processor` blocks node eviction because `minAvailable: 100%` is set on a 1-replica deployment.

## Commands
```bash
# Execute diagnosis and fixes for TR-029
kubectl -n payment-processor get all
```
