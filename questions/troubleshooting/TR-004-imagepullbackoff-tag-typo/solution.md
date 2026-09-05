# Solution for TR-004
```bash
kubectl -n warehouse set image deployment/inventory-svc web=nginx:1.25.4-alpine
kubectl -n warehouse rollout status deployment/inventory-svc
```
