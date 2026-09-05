# Solution for CA-005: Safely Drain Worker Node

Drain worker node `k3d-dev-agent-0`, ignoring DaemonSets and local storage:

```bash
kubectl drain k3d-dev-agent-0 --ignore-daemonsets --delete-emptydir-data --force
```

Verify that the node status reports `SchedulingDisabled` and workloads have been evicted:

```bash
kubectl get nodes
kubectl get pods -n maintenance-ops -o wide
```
