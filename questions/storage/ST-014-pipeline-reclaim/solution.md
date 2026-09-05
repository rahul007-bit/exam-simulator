# Solution: Decommission Worker and Retain Volume

```bash
kubectl -n storage-pipeline delete deployment pipeline-worker
kubectl -n storage-pipeline delete pvc pipeline-pvc
kubectl get pv pipeline-pv
```
