# Solution for TR-009
Option A: Label a node:
```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE disk=nvme-fast
```
Option B: Remove nodeSelector from pod YAML and recreate.
