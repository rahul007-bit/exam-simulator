# Solution for TR-035: Align Kubelet Cgroup Driver with Container Runtime

## Summary
Kubelet fails to start due to `cgroupDriver: cgroupfs` while containerd uses `systemd`. Update kubelet config to `systemd`.

## Commands
```bash
# Execute diagnosis and fixes for TR-035
kubectl -n node-runtime get all
```
