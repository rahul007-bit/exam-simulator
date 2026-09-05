# Solution for TR-039: Clear Corrupted Etcd WAL Lock on Dedicated Control Node

## Summary
Etcd static pod fails to start due to lock contention on data dir `/var/lib/etcd`. Clean lock and restore etcd member.

## Commands
```bash
# Execute diagnosis and fixes for TR-039
kubectl -n controlplane-storage get all
```
