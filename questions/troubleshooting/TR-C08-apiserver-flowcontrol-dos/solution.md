# Solution for TR-C08: Chaos: Fix FlowSchema PriorityAndFairness Self-DOS

## Summary
FlowSchema `catch-all-exempt` was modified with 0 matching seats, starving control-plane background controllers. Restore default flowschema.

## Commands
```bash
# Execute diagnosis and fixes for TR-C08
kubectl -n kube-system get all
```
