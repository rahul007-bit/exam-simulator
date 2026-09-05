# Solution for TR-C01
```bash
kubectl -n cgroup-limits describe resourcequota strict-quota
kubectl -n cgroup-limits edit deployment critical-api
```
Change requests to `cpu: 100m, memory: 128Mi` and limits to `cpu: 200m, memory: 256Mi`.
