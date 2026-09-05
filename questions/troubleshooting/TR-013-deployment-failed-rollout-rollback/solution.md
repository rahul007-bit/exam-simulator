# Solution for TR-013
```bash
kubectl -n shipping rollout history deployment/delivery-service
kubectl -n shipping rollout undo deployment/delivery-service
kubectl -n shipping rollout status deployment/delivery-service
```
