# Solution for TR-027: Add Control-Plane Toleration to Monitoring DaemonSet

## Summary
The `node-exporter` DaemonSet in `monitoring-ns` cannot run on the control-plane node because the control-plane node is tainted with `node-role.kubernetes.io/control-plane:NoSchedule`.

## Commands
Patch the DaemonSet to add the required control-plane toleration:

```bash
kubectl -n monitoring-ns patch daemonset node-exporter --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/tolerations",
    "value": [
      {
        "key": "node-role.kubernetes.io/control-plane",
        "operator": "Exists",
        "effect": "NoSchedule"
      }
    ]
  }
]'
```

Verify that `node-exporter` pods are Running across all nodes:
```bash
kubectl -n monitoring-ns get pods -o wide
```
