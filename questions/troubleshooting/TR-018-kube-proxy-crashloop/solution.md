# Solution for TR-018: Restore Kube-Proxy DaemonSet Operation

## Summary
Kube-proxy pods in `kube-system` are crashlooping due to invalid iptables mode flags in `kube-proxy` configmap. Repair configmap.

## Commands
```bash
# Execute diagnosis and fixes for TR-018
kubectl -n kube-system get all
```
