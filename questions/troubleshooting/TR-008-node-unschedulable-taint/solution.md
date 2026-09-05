# Solution for TR-008
```bash
kubectl get nodes
kubectl uncordon <node-name>
kubectl taint nodes <node-name> maintenance:NoSchedule-
kubectl -n production-apps get pods
```
